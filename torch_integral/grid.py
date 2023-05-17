import torch
import random


class Distribution(torch.nn.Module):
    def __init__(self, min_val, max_val):
        super().__init__()
        self.min_val = min_val
        self.max_val = max_val

    def sample(self):
        raise NotImplementedError(
            "Implement this method in derived class."
        )


class UniformDistribution(Distribution):
    def __init__(self, min_val, max_val):
        super().__init__(min_val, max_val)

    def sample(self):
        return random.randint(self.min_val, self.max_val)


class NormalDistribution(Distribution):
    def __init__(self, min_val, max_val):
        super(NormalDistribution, self).__init__(min_val, max_val)

    def sample(self):
        out = random.normalvariate(
            0, 0.5 * (self.max_val - self.min_val)
        )
        out = max(1, self.max_val - int(abs(out)))
        
        return out


class IGrid(torch.nn.Module):
    def __init__(self):
        super(IGrid, self).__init__()
        self.curr_grid = None
        self.size = None

    def forward(self):
        if self.curr_grid is None:
            out = self.generate_grid()
        else:
            out = self.curr_grid

        return out

    def ndim(self):
        raise NotImplementedError(
            "Implement this method in derived class."
        )

    def size(self):
        return self.size

    def generate_grid(self):
        raise NotImplementedError(
            "Implement this method in derived class."
        )


class TrainableGrid1D(IGrid):
    def __init__(self, size, init_value=None):
        super(TrainableGrid1D, self).__init__()

        if init_value is None:
            self._deltas = torch.nn.Parameter(torch.ones(size - 1))
        else:
            self._deltas = torch.nn.Parameter(init_value)

        self.generate_grid()
        self.size = size

    def ndim(self):
        return 1

    def generate_grid(self):
        device = self.deltas.device
        grid = self.deltas.abs() + 1e-8
        grid = grid / grid.sum()
        grid = grid.cumsum(0)
        self.curr_grid = torch.cat(
            [torch.tensor([0.], device=device), grid]
        )

        return self.curr_grid


class RandomUniformGrid1D(IGrid):
    def __init__(self, distribution):
        super(RandomUniformGrid1D, self).__init__()
        self.distribution = distribution
        self.size = distribution.max_val
        self.generate_grid()

    def ndim(self):
        return 1

    def _set_grid(self, size):
        self.curr_grid = torch.linspace(-1, 1, size)

    def generate_grid(self):
        if self.training:
            size = self.distribution.sample()
        else:
            size = self.size
            
        self._set_grid(size)

        return self.curr_grid

    def resize(self, new_size):
        self.size = new_size
        self.generate_grid()


class RandomTrainableGrid1D(IGrid):
    def __init__(self, distribution):
        super(RandomTrainableGrid1D, self).__init__(distribution)
        self.grids = torch.nn.ModuleDict({
            str(size): torch.nn.Parameter(torch.linspace(-1, 1, size))
            for size in range(distribution.min_val, distribution.max_val+1)
        })

    def _set_grid(self, size):
        self.curr_grid = self.grids[str(size)]


class GridND(IGrid):
    def __init__(self, grid_objects_dict):
        super(GridND, self).__init__()
        self.grid_objects = torch.nn.ModuleDict(grid_objects_dict)
        self.generate_grid()

    def ndim(self):
        return sum([
            grid.ndim() for _, grid in self.grid_objects.items()
        ])

    def reset_grid(self, dim, new_grid):
        self.grid_objects[str(dim)] = new_grid
        self.generate_grid()

    def generate_grid(self):  # CHECK AGAIN FORWARD AND GENERATE GRID
        self.curr_grid = [
            self.grid_objects[dim].generate_grid()
            for dim in self.grid_objects
        ]

        return self.curr_grid

    def forward(self):
        self.curr_grid = [
            self.grid_objects[dim]()
            for dim in self.grid_objects
        ]

        return self.curr_grid
