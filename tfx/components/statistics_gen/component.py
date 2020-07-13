# Lint as: python2, python3
# Copyright 2019 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""TFX StatisticsGen component definition."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from typing import Optional, List, Text

import absl
import tensorflow_data_validation as tfdv

from tfx import types
from tfx.components.base import base_component
from tfx.components.base import executor_spec
from tfx.components.statistics_gen import executor
from tfx.types import artifact_utils
from tfx.types import standard_artifacts
from tfx.types.standard_component_specs import StatisticsGenSpec


class StatisticsGen(base_component.BaseComponent):
  """Official TFX StatisticsGen component.

  The StatisticsGen component generates features statistics and random samples
  over training data, which can be used for visualization and validation.
  StatisticsGen uses Apache Beam and approximate algorithms to scale to large
  datasets.

  Please see https://www.tensorflow.org/tfx/data_validation for more details.

  ## Example
  ```
    # Computes statistics over data for visualization and example validation.
    statistics_gen = StatisticsGen(examples=example_gen.outputs['examples'])
  ```
  """

  SPEC_CLASS = StatisticsGenSpec
  EXECUTOR_SPEC = executor_spec.ExecutorClassSpec(executor.Executor)

  def __init__(self,
               examples: types.Channel = None,
               schema: Optional[types.Channel] = None,
               stats_options: Optional[tfdv.StatsOptions] = None,
               exclude_splits: Optional[List[Text]] = None,
               output: Optional[types.Channel] = None,
               input_data: Optional[types.Channel] = None,
               instance_name: Optional[Text] = None):
    """Construct a StatisticsGen component.

    Args:
      examples: A Channel of `ExamplesPath` type, likely generated by the
        [ExampleGen component](https://www.tensorflow.org/tfx/guide/examplegen).
        This needs to contain two splits labeled `train` and `eval`. _required_
      schema: A `Schema` channel to use for automatically configuring the value
        of stats options passed to TFDV.
      stats_options: The StatsOptions instance to configure optional TFDV
        behavior. When stats_options.schema is set, it will be used instead of
        the `schema` channel input. Due to the requirement that stats_options be
        serialized, the slicer functions and custom stats generators are dropped
        and are therefore not usable.
      exclude_splits: Names of splits where statistics and sample should not
        be generated. If exclude_splits is an empty list, no splits will be
        excluded. Default behavior is excluding no splits.
      output: `ExampleStatisticsPath` channel for statistics of each split
        provided in the input examples.
      input_data: Backwards compatibility alias for the `examples` argument.
      instance_name: Optional name assigned to this specific instance of
        StatisticsGen.  Required only if multiple StatisticsGen components are
        declared in the same pipeline.
    """
    if input_data:
      absl.logging.warning(
          'The "input_data" argument to the StatisticsGen component has '
          'been renamed to "examples" and is deprecated. Please update your '
          'usage as support for this argument will be removed soon.')
      examples = input_data
    if not output:
      statistics_artifact = standard_artifacts.ExampleStatistics()
      split_names = artifact_utils.get_single_instance(
          list(examples.get())).split_names
      for split in split_names:
        if exclude_splits and split in exclude_splits:
          split_names.remove(split)
      statistics_artifact.split_names = split_names
      output = types.Channel(
          type=standard_artifacts.ExampleStatistics,
          artifacts=[statistics_artifact])
    # TODO(b/150802589): Move jsonable interface to tfx_bsl and use json_utils.
    stats_options_json = stats_options.to_json() if stats_options else None
    spec = StatisticsGenSpec(
        examples=examples,
        schema=schema,
        stats_options_json=stats_options_json,
        exclude_splits=exclude_splits,
        statistics=output)
    super(StatisticsGen, self).__init__(spec=spec, instance_name=instance_name)
