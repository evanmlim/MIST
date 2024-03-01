import argparse
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser


def positive_int(value):
    ivalue = int(value)
    if ivalue <= 0:
        raise argparse.ArgumentTypeError(f"Argparse error. Expected a positive integer but got {value}")
    return ivalue


def non_negative_int(value):
    ivalue = int(value)
    if ivalue < 0:
        raise argparse.ArgumentTypeError(f"Argparse error. Expected a non-negative integer but got {value}")
    return ivalue


def float_0_1(value):
    fvalue = float(value)
    if not (0 <= fvalue <= 1):
        raise argparse.ArgumentTypeError(f"Argparse error. Expected a float from range (0, 1), but got {value}")
    return fvalue


def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ("yes", "true", "t", "y", "1"):
        return True
    elif v.lower() in ("no", "false", "f", "n", "0"):
        return False
    else:
        raise argparse.ArgumentTypeError("Boolean value expected!")


class ArgParser(ArgumentParser):
    def arg(self, *args, **kwargs):
        return super().add_argument(*args, **kwargs)

    def flag(self, *args, **kwargs):
        return super().add_argument(*args, action="store_true", **kwargs)

    def boolean_flag(self, *args, **kwargs):
        return super().add_argument(*args, type=str2bool, nargs="?", const=True, metavar="BOOLEAN", **kwargs)


def get_main_args():
    p = ArgParser(formatter_class=ArgumentDefaultsHelpFormatter)

    # Runtime
    p.arg("--exec-mode",
          type=str,
          default="all",
          choices=["all", "analyze", "preprocess", "train"],
          help="Run all of the MIST pipeline or an individual component"),
    p.arg("--data", type=str, help="Path to dataset json file")
    p.arg("--gpus", nargs="+", default=[-1], type=int, help="Which gpu(s) to use, defaults to all available GPUs")
    p.arg("--num-workers", type=positive_int, default=8, help="Number of workers to use for data loading")
    p.arg("--master-port", type=str, default="12355", help="Master port for multi-gpu training")
    p.arg("--seed_val", type=non_negative_int, default=42, help="Random seed")
    p.boolean_flag("--tta", default=False, help="Enable test time augmentation")

    # Output
    p.arg("--results", type=str, help="Path to output of MIST pipeline")
    p.arg("--numpy", type=str, help="Path to save preprocessed numpy data")

    # AMP
    p.boolean_flag("--amp", default=False, help="Enable automatic mixed precision (recommended)")

    # Training hyperparameters
    p.arg("--batch-size", type=positive_int, default=2, help="Batch size")
    p.arg("--patch-size", nargs="+", type=int, help="Height, width, and depth of patch size")
    p.arg("--max-patch-size", default=[256, 256, 128], nargs="+", type=int, help="Max patch size")
    p.arg("--learning-rate", type=float, default=0.0003, help="Learning rate")
    p.arg("--exp_decay", type=float, default=0.9, help="Exponential decay factor")
    p.arg("--lr-scheduler",
          type=str,
          default="constant",
          choices=["constant", "cosine_warm_restarts", "exponential"],
          help="Learning rate scheduler")
    p.arg("--cosine-first-steps",
          type=positive_int,
          default=500,
          help="Length of a cosine decay cycle in steps, only with cosine_annealing scheduler")

    # Optimizer
    p.arg("--optimizer", type=str, default="adam", choices=["sgd", "adam", "adamw"], help="Optimizer")
    p.boolean_flag("--clip-norm", default=False, help="Use gradient clipping")
    p.arg("--clip-norm-max", type=float, default=1.0, help="Max threshold for global norm clipping")

    # Neural network parameters
    p.arg("--model",
          type=str,
          default="nnunet",
          choices=["nnunet", "unet", "fmgnet", "wnet", "attn_unet", "unetr"])
    p.boolean_flag("--use-res-block", default=False, help="Use residual blocks for nnUNet or UNet")
    p.boolean_flag("--pocket", default=False, help="Use pocket version of network")
    p.arg("--depth", type=non_negative_int, help="Depth of U-Net or similar architecture")
    p.boolean_flag("--deep-supervision", default=False, help="Use deep supervision")
    p.arg("--deep-supervision-heads", type=positive_int, default=2, help="Number of deep supervision heads")
    p.boolean_flag("--vae-reg", default=False, help="Use VAE regularization")
    p.arg("--vae-penalty", type=float_0_1, default=0.01, help="Weight for VAE regularization loss")
    p.boolean_flag("--l2-reg", default=False, help="Use L2 regularization")
    p.arg("--l2-penalty", type=float_0_1, default=0.00001, help="L2 penalty")
    p.boolean_flag("--l1-reg", default=False, help="Use L1 regularization")
    p.arg("--l1-penalty", type=float_0_1, default=0.00001, help="L1 penalty")

    # Data loading
    p.arg("--oversampling",
          type=float_0_1,
          default=0.4,
          help="Probability of crop centered on foreground voxel")

    # Preprocessing
    p.boolean_flag("--no-preprocess", default=False, help="Turn off preprocessing")
    p.boolean_flag("--use-n4-bias-correction", default=False, help="Use N4 bias field correction (only for MR images)")
    p.boolean_flag("--use-config-class-weights", default=False, help="Use class weights in config file")
    p.arg("--class-weights", nargs="+", type=float, help="Specify class weights")

    # Loss function
    p.arg("--loss",
          type=str,
          default="dice_ce",
          choices=["dice_ce", "dice", "gdl", "gdl_ce"],
          help="Loss function for training")

    # Sliding window inference
    p.arg("--sw-overlap",
          type=float_0_1,
          default=0.25,
          help="Amount of overlap between scans during sliding window inference")
    p.arg("--blend-mode",
          type=str,
          choices=["constant", "gaussian"],
          default="gaussian",
          help="How to blend output of overlapping windows")

    # Postprocessing
    p.boolean_flag("--no-postprocess", default=False, help="Run post processing on MIST output")

    # Validation
    p.arg("--nfolds", type=positive_int, default=5, help="Number of cross-validation folds")
    p.arg("--folds", nargs="+", default=[0, 1, 2, 3, 4], type=int, help="Which folds to run")
    p.arg("--epochs", type=positive_int, default=1000, help="Number of epochs")
    p.arg("--steps-per-epoch",
          type=positive_int,
          help="Steps per epoch. By default ceil(training_dataset_size / batch_size / gpus)")

    # Evaluation
    p.boolean_flag("--use-native-spacing",
                   default=False,
                   help="Use native image spacing to compute Hausdorff distances")

    # Uncertainty
    p.boolean_flag("--output-std", default=False, help="Output standard deviation for ensemble predictions")

    args = p.parse_args()
    return args