# Copyright (C) 2022 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Module for dealing with the hekit configuration file"""

from os import path
from typing import NamedTuple

from tomlkit import string
from kit.utils.files import load_toml
from pydantic import BaseModel, validator

class Config(NamedTuple, BaseModel):
    """Represents a config"""

    config_filename: str
    repo_location: str

    @validator('config_filename')
    def config_filename_is_string(cls, v):
      if len(v) == 0:
        raise ValueError('must not be empty')
      return v
    @validator('repo_location')
    def repo_location_is_string(cls, v):
      if len(v) == 0:
        raise ValueError('must not be empty')
      return v

class ConfigFileError(Exception):
    """Error for when config file is not constructed correctly"""


def config_required(func):
    """Decorator that loads the config file before running the actual function"""

    def inner(args):
        # replace the filename with the actual config
        args.config = load_config(args.config)
        return func(args)

    return inner


def load_config(filename: str) -> Config:
    """Load a config file in TOML format"""
    expand = path.expanduser  # alias

    try:
        toml_dict = load_toml(filename)
        toml_dict = {k: expand(v) for k, v in toml_dict.items()}
    except Exception as e:
        raise ConfigFileError("Error while parsing config file\n", f"  {e!r}") from e

    # deref kwargs this way, get exceptions unknown key for free
    return Config(expand(filename), **toml_dict)
