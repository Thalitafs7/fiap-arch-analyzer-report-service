#!/bin/bash

# .github/scripts/check_test_success.sh
# Script to standardize test execution and check for success.

TEST_COMMAND=$1

if [ -z "$TEST_COMMAND" ]; then
  echo "Error: No test command provided."
  exit 1
fi

echo "Running tests: $TEST_COMMAND"
eval $TEST_COMMAND
TEST_EXIT_CODE=$?

if [ $TEST_EXIT_CODE -eq 0 ]; then
  echo "Tests passed successfully!"
  exit 0
else
  echo "Tests failed with exit code $TEST_EXIT_CODE."
  exit $TEST_EXIT_CODE
fi
