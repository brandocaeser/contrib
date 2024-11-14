import mindspore as ms
from mindspore import Tensor, ops
import numpy as np

class SVGD_model():
    def __init__(self):
        pass

    def SVGD_kernel(self, x, h=-1):
        
        x_norm = ops.ReduceSum(keep_dims=True)(x ** 2, axis=1)
        pairwise_dists = x_norm - 2 * ops.matmul(x, x.T) + x_norm.T

        if h < 0:  
            pairwise_dists_np = pairwise_dists.asnumpy()
            h_value = np.median(pairwise_dists_np)
            h = Tensor(h_value ** 2 / np.log(x.shape[0] + 1), ms.float32)
        else:
            h = Tensor(h, ms.float32)

        kernel_xj_xi = ops.exp(-pairwise_dists ** 2 / h)

        x_expand = x[:, None, :]  
        x_diff = x_expand - x[None, :, :] 
        weights = kernel_xj_xi[:, :, None] 
        weighted_diff = weights * x_diff
        d_kernel_xi = ops.ReduceSum()(weighted_diff, axis=1) * 2 / h

        return kernel_xj_xi, d_kernel_xi

    def update(self, x0, lnprob, n_iter=1000, stepsize=1e-3, bandwidth=-1, alpha=0.9, debug=False):
        if x0 is None or lnprob is None:
            raise ValueError('x0 or lnprob cannot be None!')

        x = x0.copy()
        eps_factor = 1e-8
        historical_grad_square = None

        for iter in range(n_iter):
            if debug and (iter + 1) % 100 == 0:
                print('iter ' + str(iter + 1))

            kernel_xj_xi, d_kernel_xi = self.SVGD_kernel(x, h=bandwidth)
            grad_lnprob = lnprob(x)

            current_grad = (ops.matmul(kernel_xj_xi, grad_lnprob) + d_kernel_xi) / x.shape[0]

            if historical_grad_square is None:
                historical_grad_square = current_grad ** 2
            else:
                historical_grad_square = alpha * historical_grad_square + (1 - alpha) * (current_grad ** 2)

            adj_grad = current_grad / ops.sqrt(historical_grad_square + eps_factor)
            x += stepsize * adj_grad

        return x

