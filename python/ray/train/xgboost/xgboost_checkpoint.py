import os
import tempfile
from typing import TYPE_CHECKING, Optional

import xgboost

from ray.air._internal.checkpointing import save_preprocessor_to_dir
from ray.air.checkpoint import Checkpoint
from ray.air.constants import MODEL_KEY
from ray.train._internal.framework_checkpoint import FrameworkCheckpoint
from ray.util.annotations import PublicAPI

if TYPE_CHECKING:
    from ray.data.preprocessor import Preprocessor


@PublicAPI(stability="beta")
class XGBoostCheckpoint(FrameworkCheckpoint):
    """A :py:class:`~ray.train.Checkpoint` with XGBoost-specific functionality."""

    MODEL_FILENAME = "model.pkl"

    @classmethod
    def from_model(
        cls,
        booster: xgboost.Booster,
        *,
        preprocessor: Optional["Preprocessor"] = None,
    ) -> "XGBoostCheckpoint":
        """Create a :py:class:`~ray.air.checkpoint.Checkpoint` that stores an XGBoost
        model.

        Args:
            booster: The XGBoost model to store in the checkpoint.
            preprocessor: A fitted preprocessor to be applied before inference.

        Returns:
            An :py:class:`XGBoostCheckpoint` containing the specified ``Estimator``.

        Examples:

            ... testcode::

                import numpy as np
                import ray
                from ray.train.xgboost import XGBoostCheckpoint
                import xgboost

                train_X = np.array([[1, 2], [3, 4]])
                train_y = np.array([0, 1])

                model = xgboost.XGBClassifier().fit(train_X, train_y)
                checkpoint = XGBoostCheckpoint.from_model(model.get_booster())

        """
        tmpdir = tempfile.mkdtemp()
        booster.save_model(os.path.join(tmpdir, cls.MODEL_FILENAME))

        checkpoint = cls.from_directory(tmpdir)
        if preprocessor:
            checkpoint.set_preprocessor(preprocessor)
        return checkpoint

    def get_model(self) -> xgboost.Booster:
        """Retrieve the XGBoost model stored in this checkpoint."""
        with self.as_directory() as checkpoint_path:
            booster = xgboost.Booster()
            booster.load_model(os.path.join(checkpoint_path, self.MODEL_FILENAME))
            return booster


@PublicAPI(stability="beta")
class LegacyXGBoostCheckpoint(Checkpoint):
    """A :py:class:`~ray.air.checkpoint.Checkpoint` with XGBoost-specific
    functionality.

    Create this from a generic :py:class:`~ray.air.checkpoint.Checkpoint` by calling
    ``XGBoostCheckpoint.from_checkpoint(ckpt)``.
    """

    @classmethod
    def from_model(
        cls,
        booster: xgboost.Booster,
        *,
        preprocessor: Optional["Preprocessor"] = None,
    ) -> "XGBoostCheckpoint":
        """Create a :py:class:`~ray.air.checkpoint.Checkpoint` that stores an XGBoost
        model.

        Args:
            booster: The XGBoost model to store in the checkpoint.
            preprocessor: A fitted preprocessor to be applied before inference.

        Returns:
            An :py:class:`XGBoostCheckpoint` containing the specified ``Estimator``.

        Examples:

            ... testcode::

                import numpy as np
                import ray
                from ray.train.xgboost import XGBoostCheckpoint
                import xgboost

                train_X = np.array([[1, 2], [3, 4]])
                train_y = np.array([0, 1])

                model = xgboost.XGBClassifier().fit(train_X, train_y)
                checkpoint = XGBoostCheckpoint.from_model(model.get_booster())

            You can use a :py:class:`XGBoostCheckpoint` to create an
            :py:class:`~ray.train.xgboost.XGBoostPredictor` and preform inference.

            ... testcode::

                from ray.train.xgboost import XGBoostPredictor
                predictor = XGBoostPredictor.from_checkpoint(checkpoint)

        """
        with tempfile.TemporaryDirectory() as tmpdirname:
            booster.save_model(os.path.join(tmpdirname, MODEL_KEY))

            if preprocessor:
                save_preprocessor_to_dir(preprocessor, tmpdirname)

            checkpoint = cls.from_directory(tmpdirname)
            ckpt_dict = checkpoint.to_dict()

        return cls.from_dict(ckpt_dict)

    def get_model(self) -> xgboost.Booster:
        """Retrieve the XGBoost model stored in this checkpoint."""
        with self.as_directory() as checkpoint_path:
            booster = xgboost.Booster()
            booster.load_model(os.path.join(checkpoint_path, MODEL_KEY))
            return booster
