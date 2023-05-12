import torch
from py2opt.routefinder import RouteFinder


class BasePermutation():
    def __init__(self):
        pass

    def permute(self, tensors, size):
        permutation = self.find_permutation(tensors, size)

        for t in tensors:
            dim = t['dim']
            tensor = t['value']
            tensor.data = torch.index_select(
                tensor.data, dim, permutation
            )

    def find_permutation(self, tensors, size):
        raise NotImplementedError(
            "Implement this method in derived class."
        )

    def dist_function(self, x, y):
        raise NotImplementedError(
            "Implement this method in derived class."
        )


class NOptPermutation(BasePermutation):
    def __init__(self, iters=500):
        super(NOptPermutation, self).__init__()
        self.iters = iters

    def find_permutation(self, tensors, size):
        cities_names = [i for i in range(size)]
        dist_mat = self.distance_matrix(tensors, size)
        route_finder = RouteFinder(
            dist_mat, cities_names, iterations=self.iters
        )
        best_distance, indices = route_finder.solve()
        indices = torch.tensor(indices)

        return indices

    def dist_function(self, x, y):
        """
        """
        return (x - y).abs().mean()

    def distance_matrix(self, tensors, size):
        """
        """
        mat = []

        for i in range(size):
            n = list()
            mat.append(n)

            for j in range(size):
                dist = 0.0

                for t in tensors:
                    tensor = t['value']
                    dim = t['dim']
                    x_i = torch.select(tensor, dim, i)
                    x_j = torch.select(tensor, dim, j)
                    dist += float(self.dist_function(x_i, x_j))

                mat[i].append(dist)

        return mat
