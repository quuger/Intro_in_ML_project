import torch
# import torch_npu # No longer needed in torch_npu 2.5.1 and later versions

x = torch.randn(2, 2).npu()
y = torch.randn(2, 2).npu()
z = x.mm(y)

print(z)
