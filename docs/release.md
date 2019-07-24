# Release Workflow

## Overview

Release workflow is engined by Jenkins and described by the [pipeline](../devops/aws-codebuild/Jenkinsfile.cd).

For now release artifacts are created only for debian package [repository](https://repo.sovrin.org/deb/)
maintained by [The Sovrin Foundation](https://sovrin.org)

There are several types of releases:
- `dev` releases are built for each commit to `master` branch;
- `rc` (release candidate) releases are built for each commit to `stable` when `indy-node` dependency is set to *non stable* version;
- `stable` releases are built for each commit to `stable` branch when `indy-node` dependency is set to *stable* version.

## Release Pipeline

1. Preparation
    1. `indy-node` dependency version is checked in [sovtoken/setup.py](../sovtoken/setup.py).
    2. Necessary AWS resources are created.
2. Build
    1. AWS CodeBuild project builds debian packages for each plugin
3. Publishing and Notification
    1. The packages are published to a debian repository channel. The channel depends on `indy-node` dependency version and GitHub branch:
        - `master` commits are published to `master` debian channel, debian packages include unique pipeline build number as part of their versions (e.g. `1.0.0~dev65`).
        - `stable` commits are published:
            - to `rc` channel if `indy-node` version is *non stable* (e.g. `1.8.0~rc1`);
            - to `stable` channel otherwise.
        - Note. `stable` packages' versions match ones from the source code (e.g. `0.9.13`) and `rc` packages will have additional suffix (e.g. `0.9.14~rc10`).

## Release Workflow

1. Release candidate preparation
    1. [**Contributor**]
        - Create a branch from `stable`.
        - Merge necessary changes from `master`;
        - Wait for `indy-node` release candidate and set its version in [sovtoken/setup.py](../sovtoken/setup.py) and [devops/Makefile](../devops/Makefile).
        - Create a pull request to `stable`.
    2. [**build server**]
        - Run CI for the PR.
    3. [**Maintainer**]
        - Review, approve and merge the PR.
    4. [**build server**]
        - Once PR is merged start the [release pipeline](#release-pipeline) which will publish debian packages to `rc` repo component.
2. Release candidate acceptance
    1. [**QA**]
        - (_optional_) Perform additional testing. If the candidate is rejected next one is prepared repeating steps described above.
3. Releasing
    1. [**Contributor**]
        - Once QA accepts and `indy-node` is released create a branch from `stable`.
        - Set `indy-node` dependency version to stable one.
        - Create new PR to `stable`.
    2. [**build server**]
        - Run CI for the PR.
    3. [**Maintainer**]
        - Review, approve and merge the PR.
    4. [**build server**]
        - Run [release pipeline](#release-pipeline) which publishes debian packages to `stable` repo component.
4. New Development Cycle Start
    1. [**Contributor**]
        - Create a PR with version bumps in [sovtoken/__metadata__.py](../sovtoken/sovtoken/__metadata__.py) and [sovtokenfees/__metadata__.py](../sovtokenfees/sovtokenfees/__metadata__.py).
