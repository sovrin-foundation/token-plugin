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

## Release Workflow

1. Release candidate preparation
    1. [**Contributor**]
        - Creates a branch from `stable`.
        - Merges necessary changes from `master`;
        - Waits for `indy-node` release candidate is released and set its versions in [sovtoken/setup.py](../sovtoken/setup.py) and [devops/Makefile](../devops/Makefile).
        - Creates a pull request to `stable`.
    2. [**Maintainer**] once CI testing is passed reviews, approves and merges the PR.
    3. [**build server**]
        - Once PR is merged starts the [release pipeline](#release-pipeline) which publishes debian packages to `rc` repo component.
2. Release candidate acceptance
    1. [**QA**]
        - Waits for `sovrin` release candidate and performs acceptance of the coming release verifying a full software stack: `indy-node`, `token-plugin` and `sovrin`.
        - If QA rejects new release new candidates are prepared repeating steps described above.
3. Releasing
    1. [**Contributor**]
        - Once QA accepts and `indy-node` is released creates a branch from `stable`.
        - Sets `indy-node` dependency version to stable one.
        - Creates new PR to `stable`.
    2. [**Maintainer**] once CI testing is passed, reviews, approves and merges that PR.
    3. [**build server**]
        - Once PR is merged starts the [release pipeline](#release-pipeline) which publishes debian packages to `stable` repo component.


### Important Note

Commits to `stable` with plugins versions and `indy-node` version that were already published can't be published again since release logic detects duplicates in the debian repository and skips publishing for such cases.
