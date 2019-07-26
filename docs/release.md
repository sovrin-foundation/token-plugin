# Release Workflow

## Overview

Release workflow is engined by Jenkins and described by the [pipeline](../devops/aws-codebuild/Jenkinsfile.cd).

Release pipeline is [run](https://build.sovrin.org/job/token-plugin/job/token-plugin-cd/) by the Sovrin Foundation Jenkins server.

For now release artifacts are created only for debian package [repository](https://repo.sovrin.org/deb/)
maintained by [The Sovrin Foundation](https://sovrin.org).

There are several release types:
- `dev` releases are built for each commit into `master` branch, artifacts are published to `master` debian channel;
- `rc` (release candidate) releases are built for each commit into `stable` when `indy-node` dependency is set to _non stable_ version, artifacts are published to `rc` debian channel;
- `stable` releases are built for each commit into `stable` branch when `indy-node` dependency is set to _stable_ version, artifacts are published to `rc` and if approved to `stable` channel as well.

## Release Pipeline

1. Preparation
    1. `indy-node` dependency version is checked in [sovtoken/setup.py](../sovtoken/setup.py).
    2. Release type is selected depending on branch and `indy-node` version:
        - `dev` for `master` branch;
        - `rc` for `stable` branch if `indy-node` version is non stable (e.g. `1.8.0~rc1`);
        - `stable` for `stable` branch if `indy-node` version is stable.
    3. Debian packages versions are set as follows:
        - `X.Y.Z~devB` for `dev` release (`X.Y.Z` is a versions from [sovtoken/\_\_metadata__.py](../sovtoken/sovtoken/__metadata__.py) and [sovtokenfees/\_\_metadata__.py](../sovtokenfees/sovtokenfees/__metadata__.py) files, `B` is a Jenkins build number);
        - `X.Y.Z~rcB` for `rc` release;
        - `X.Y.Z` for `stable` one.
    4. Necessary AWS resources are created.
2. Build
    1. AWS CodeBuild project builds debian packages for each plugin.
3. Publishing and Notification
    1. The packages are published to a debian repository channels depending on the release type:
        - `dev` release - `master` channel;
        - `rc` release - `rc` channel;
        - `stable` release - `rc` channel and if approved to `stable` channel as well.

## Release Workflow

### Release `rc`

1. Release Candidate Preparation
    1. [**Contributor**]
        - Create a branch from `stable`.
        - Apply necessary changes from `master` (either `merge` or `cherry-pick`).
        - Set `indy-node` **release candidate** version in [sovtoken/setup.py](../sovtoken/setup.py) and `FPM_P_DEPENDS` variable in  [devops/Makefile](../devops/Makefile).
        - Create a pull request to `stable`.
    2. [**build server**]
        - Run CI for the PR.
    3. [**Maintainer**]
        - Review, approve and merge the PR. That triggers the pipeline.
    4. [**build server**]
        - Run the [release pipeline](#release-pipeline) which will publish debian packages to `rc` debian repo component.
2. Release Candidate Acceptance
    1. [**QA**]
        - (_optional_) Perform additional testing. If the candidate is rejected next one is prepared repeating the steps described above.
3. Stable Release Issuing
    - if QA accepts the release candidate and `indy-node` is released [stable release](#release-stable) might be started.

### Release `stable`

1. Release Candidate Preparation
    - The steps are similar to [rc release](#release-rc) except the following:
        - stable `indy-node` version is set;
        - once `build server` publishes release candidate packages to `rc` channel it starts waiting for an approval to perform additional steps.
2. Release Candidate Acceptance
    1. [**QA**]
        - (_optional_) Additional testing.
    2. [**QA/Maintainer**]
        - Once QA accepts the release candidate allow the pipeline to proceed.
3. Releasing
    1. [**build server**]
        - Publish the packages to `stable` debian component.
    2. [**Maintainer**]
        - Set a tag and add release notes in GitHub.
4. New Development Cycle Start
    1. [**Contributor**]
        - Create a PR with version bumps in [sovtoken/\_\_metadata__.py](../sovtoken/sovtoken/__metadata__.py) and [sovtokenfees/\_\_metadata__.py](../sovtokenfees/sovtokenfees/__metadata__.py).
