# Release Workflow

## Overview

Release workflow is engined by Jenkins and described by the [pipeline](../devops/aws-codebuild/Jenkinsfile.cd).

For now release artifacts are created only for debian package [repository](https://repo.sovrin.org/deb/)
maintained by [The Sovrin Foundation](https://sovrin.org)

There are several types of releases:
- dev releases are built for each commit to `master` branch;
- rc (release candidate) releases are built for each commit to `stable` when `indy-node` dependency is set to *non stable* version;
- stable releases are built for each commit to `stable` branch when `indy-node` dependency is set to *stable* version.

## Release Pipeline

1. Preparation
    1. `indy-node` version is checked.
    2. Necessary AWS resources are created.
2. Build
    1. AWS CodeBuild project builds debian packages for each plugin
3. Publishing and Notification
    1. Built packages are published to the repository component depending on the `indy-node` dependency version and GitHub branch as it was mentioned above:
        - `master` commits are published to `master`, debian packages include unique pipeline build number as part of their versions.
        - `stable` commits are published to `rc` if `indy-node` version is *non stable* (e.g. `1.8.0~rc1`) and to `stable` otherwise. These artifacts' versions match ones from the source code.

### Important Note

Commits to `stable` with plugins versions and `indy-node` version that were already published can't be published again since release logic detects duplicates in the debian repository and skips publishing for such cases.
