# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for ScalingTensor."""

import unittest
import torch

from msamp.common.dtype import Dtypes
from msamp.common.tensor import TypeCast
from msamp.common.tensor import ScalingMeta
from msamp.common.tensor import ScalingTensor
from tests.helper import decorator


class ScalingTensorTestCase(unittest.TestCase):
    """Test ScalingTensor."""
    def setUp(self):
        """Hook method for setting up the test fixture before exercising it."""
        torch.manual_seed(100)
        self.size = (4, 4)
        self.device = 'cuda'

    def tearDown(self):
        """Hook method for deconstructing the test fixture after testing it."""
        pass

    @decorator.cuda_test
    def test_torch_tensor_cast(self):
        """Test overrided tensor.cast functions."""
        tensor = torch.randn(self.size, device=self.device)

        supported_qtype_dtypes = {
            Dtypes.kfloat8_e4m3: torch.uint8,
            Dtypes.kfloat8_e5m2: torch.uint8,
            Dtypes.kfloat16: torch.float16,
            Dtypes.kfloat32: torch.float32
        }

        for qtype, dtype in supported_qtype_dtypes.items():
            scaling_tensor = tensor.cast(qtype)
            self.assertTrue(scaling_tensor.dtype == dtype)
            self.assertTrue(scaling_tensor.qtype == qtype)

        with self.assertRaises(TypeError):
            tensor.cast(Dtypes.kbfloat16)

    @decorator.cuda_test
    def test_torch_unary_funcs(self):
        """Test overrided tensor unary functions."""
        tensor = torch.randn(self.size, device=self.device)
        scaling_tensor = tensor.cast(Dtypes.kfloat8_e4m3)

        # test torch.zero_like
        zero_tensor = torch.zeros(self.size, device=self.device)
        self.assertTrue(torch.equal(zero_tensor, torch.zeros_like(scaling_tensor)))
        self.assertTrue(torch.equal(zero_tensor, torch.zeros_like(tensor)))

        # test torch.ones_like
        one_tensor = torch.ones(self.size, device=self.device)
        self.assertTrue(torch.equal(one_tensor, torch.ones_like(scaling_tensor)))
        self.assertTrue(torch.equal(one_tensor, torch.ones_like(tensor)))

    @decorator.cuda_test
    def test_tensor_basic_funcs(self):
        """Test basic functions in ScalingTensor."""
        tensor = torch.randn(self.size, device=self.device)
        meta = ScalingMeta(Dtypes.kfloat8_e4m3)
        scaling_tensor = ScalingTensor(TypeCast.cast_to_fp8(tensor, meta), meta=meta)

        self.assertTrue(scaling_tensor.grad is None)
        self.assertTrue(scaling_tensor.is_cuda)
        self.assertEqual(scaling_tensor.shape, self.size)
        self.assertEqual(scaling_tensor.size(), self.size)
        self.assertEqual(scaling_tensor.numel(), self.size[0] * self.size[1])
        self.assertEqual(scaling_tensor.device, tensor.device)
        self.assertEqual(scaling_tensor.dtype, torch.uint8)
        self.assertEqual(scaling_tensor.type(), 'msamp.common.tensor.tensor.ScalingTensor')
        self.assertTrue(scaling_tensor.is_leaf)
        self.assertFalse(scaling_tensor.is_sparse)
        self.assertTrue(scaling_tensor.is_contiguous())
        self.assertFalse(scaling_tensor.is_complex())
        self.assertEqual(len(scaling_tensor), self.size[0])

    @decorator.cuda_test
    def test_is_floating_point(self):
        """Test is_floating_point function in ScalingTensor."""
        tensor = torch.randn(self.size, device=self.device)
        scaling_tensor = tensor.cast(Dtypes.kfloat8_e4m3)
        self.assertEqual(torch.is_floating_point(scaling_tensor), scaling_tensor.is_floating_point())

    @decorator.cuda_test
    def test_tensor_to(self):
        """Test to function in ScalingTensor."""
        tensor = torch.randn(self.size, device=self.device)
        scaling_tensor = tensor.cast(Dtypes.kfloat8_e4m3)

        supported_dtypes = [torch.float, torch.float16, torch.bfloat16]
        for dtype in supported_dtypes:
            tensor = scaling_tensor.to(dtype)
            self.assertEqual(type(tensor), torch.Tensor)
            self.assertEqual(tensor.dtype, dtype)

        with self.assertRaises(TypeError):
            scaling_tensor.to(torch.uint8)

        # test unique dtype
        with self.assertRaises(TypeError):
            scaling_tensor.to(torch.float16, torch.float32)

    @decorator.cuda_test
    def test_tensor_cast(self):
        """Test cast function in ScalingTensor."""
        tensor = torch.randn(self.size, device=self.device)
        scaling_tensor = tensor.cast(Dtypes.kfloat32)
        # kfloat32 can cast to any valid qtype
        self.assertEqual(scaling_tensor.cast(Dtypes.kfloat8_e4m3).qtype, Dtypes.kfloat8_e4m3)
        self.assertEqual(scaling_tensor.cast(Dtypes.kfloat8_e5m2).qtype, Dtypes.kfloat8_e5m2)
        self.assertEqual(scaling_tensor.cast(Dtypes.kfloat16).qtype, Dtypes.kfloat16)
        self.assertEqual(scaling_tensor.cast(Dtypes.kfloat32).qtype, Dtypes.kfloat32)

        # kfloat16 can cast to kfloat8_e4m3 kfloat16 kfloat32
        scaling_tensor = tensor.cast(Dtypes.kfloat16)
        self.assertEqual(scaling_tensor.cast(Dtypes.kfloat8_e4m3).qtype, Dtypes.kfloat8_e4m3)
        self.assertEqual(scaling_tensor.cast(Dtypes.kfloat16).qtype, Dtypes.kfloat16)
        self.assertEqual(scaling_tensor.cast(Dtypes.kfloat32).qtype, Dtypes.kfloat32)
        with self.assertRaises(TypeError):
            scaling_tensor.cast(Dtypes.kfloat8_e5m2)

        # kfloat8_e4m3 can cast to kfloat8_e4m3 kfloat32
        scaling_tensor = tensor.cast(Dtypes.kfloat8_e4m3)
        self.assertEqual(scaling_tensor.cast(Dtypes.kfloat8_e4m3).qtype, Dtypes.kfloat8_e4m3)
        self.assertEqual(scaling_tensor.cast(Dtypes.kfloat32).qtype, Dtypes.kfloat32)
        with self.assertRaises(TypeError):
            scaling_tensor.cast(Dtypes.kfloat16)
        with self.assertRaises(TypeError):
            scaling_tensor.cast(Dtypes.kfloat8_e5m2)

    @decorator.cuda_test
    def test_tensor_mul(self):
        """Test mul function in ScalingTensor."""
        tensor = torch.randn(self.size, device=self.device)
        scaling_tensor = tensor.cast(Dtypes.kfloat8_e4m3)
        float_tensor1 = scaling_tensor.float()
        scaling_tensor.mul_(torch.tensor((2.0, ), device=self.device))
        float_tensor2 = scaling_tensor.float()

        self.assertTrue(torch.equal(float_tensor1 * 2.0, float_tensor2))
        scaling_tensor.mul_(2.0)
        scaling_tensor3 = scaling_tensor.float()
        self.assertTrue(torch.equal(float_tensor2 * 2.0, scaling_tensor3))

    @decorator.cuda_test
    def test_tensor_div(self):
        """Test div function in ScalingTensor."""
        tensor = torch.randn(self.size, device=self.device)
        scaling_tensor = tensor.cast(Dtypes.kfloat8_e4m3)
        float_tensor1 = scaling_tensor.float()
        scaling_tensor.div_(torch.tensor((2.0, ), device=self.device))
        float_tensor2 = scaling_tensor.float()
        self.assertTrue(torch.equal(float_tensor1 / 2.0, float_tensor2))
        scaling_tensor.div_(2.0)
        float_tensor3 = scaling_tensor.float()
        self.assertTrue(torch.equal(float_tensor2 / 2.0, float_tensor3))

    @decorator.cuda_test
    def test_tensor_transpose(self):
        """Test transpose function in ScalingTensor."""
        tensor = torch.randn(self.size, device=self.device)
        scaling_tensor = tensor.cast(Dtypes.kfloat8_e4m3)
        float_tensor = scaling_tensor.float()
        transpose_tensor_value = scaling_tensor.t().contiguous().float()
        self.assertTrue(torch.equal(float_tensor.t(), transpose_tensor_value))

    @decorator.cuda_test
    def test_inf_and_nan(self):
        """Test has_inf_or_nan function in ScalingTensor."""
        tensor = torch.tensor([1, 2, 3, 4, 5], dtype=torch.float32, device=self.device)
        scaling_tensor = tensor.cast(Dtypes.kfloat8_e4m3)
        self.assertFalse(scaling_tensor.has_inf_or_nan())

        tensor = torch.tensor([1, 2, 3, 4, 5, torch.inf], dtype=torch.float32, device=self.device)
        scaling_tensor = tensor.cast(Dtypes.kfloat8_e4m3)
        self.assertTrue(scaling_tensor.has_inf_or_nan())

        tensor = torch.tensor([1, 2, 3, 4, 5, torch.nan], dtype=torch.float32, device=self.device)
        scaling_tensor = tensor.cast(Dtypes.kfloat8_e4m3)
        self.assertTrue(scaling_tensor.has_inf_or_nan())

    @decorator.cuda_test
    def test_tensor_zero(self):
        """Test zero function in ScalingTensor."""
        tensor = torch.randn(self.size, device=self.device)
        scaling_tensor = tensor.cast(Dtypes.kfloat8_e4m3)
        scaling_tensor.zero_()
        self.assertTrue((scaling_tensor.float() == 0).all())

    @decorator.cuda_test
    def test_tensor_min_max(self):
        """Test min and max function in ScalingTensor."""
        tensor = torch.randn(self.size, device=self.device)
        scaling_tensor = tensor.cast(Dtypes.kfloat8_e4m3)
        self.assertEqual(scaling_tensor.max().item(), scaling_tensor.float().max().item())
        self.assertEqual(scaling_tensor.min().item(), scaling_tensor.float().min().item())
