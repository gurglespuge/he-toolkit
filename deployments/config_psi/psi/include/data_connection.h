/* Copyright (C) 2022 Intel Corporation
 * SPDX-License-Identifier: Apache-2.0
 */

#pragma once

class DataConnection {
 public:
  // Connect to data layer
  virtual void connect() = 0;

  // Disconnect from data layer
  virtual void disconnect() = 0;

  // Read in data
  virtual void read() = 0;

  // Write out data
  virtual void write() = 0;

  // Process data
  virtual void process() = 0;

  virtual ~DataConnection() = default;
};
