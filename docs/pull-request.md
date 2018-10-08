
# Table of Contents

1.  [Pull Request](#orgb6b25a7)
    1.  [Types of pull request](#org011316d)
        1.  [Type one: Changes to the code base](#org185f1e5)
        2.  [Type two: Dependency changes](#orgd9a5907)
        3.  [Type three: Changes to Devops](#org9436233)
    2.  [Approving changes](#org55c0274)
        1.  [What is the approval process?](#orgdf3e819)


<a id="orgb6b25a7"></a>

# Pull Request


<a id="org011316d"></a>

## Types of pull request


<a id="org185f1e5"></a>

### Type one: Changes to the code base

These pull request are changes to any file that deals with logic and
function of the plugin. These include but are not limited to: 

-   new features
-   bug fixes
-   documentation changes

1.  Rules

    1.  Anyone in the community can make these pull requests
    2.  The pull request needs to:
        -   Pass all tests through jenkins
        -   Have at least two approvals from maintainers


<a id="orgd9a5907"></a>

### Type two: Dependency changes

For now we have decided that the sovrin-plugin will work on the latest stable
builds of its dependencies (this can change if necessary).

1.  Rules

    1.  Anyone in the community can make these pull requests
    2.  The pull request needs to:
        -   have a clearly-documented explanation of why versions should change
        -   Pass all tests through jenkins
        -   Have <span class="underline">all</span> maintainers approve of the change


<a id="org9436233"></a>

### Type three: Changes to Devops

This includes changes to any files in the devops folder. Please note that
the community should not make changes to these files because they are for
internal use only.

1.  Rules

    1.  Only internal entities should make these pull requests
    2.  The pull request needs to:
        -   Pass all tests through jenkins
        -   Have at least 2 maintainers approve of the change


<a id="org55c0274"></a>

## Approving changes


<a id="orgdf3e819"></a>

### What is the approval process?

1.  A maintainer must thoroughly read and consider the impact of proposed

changes

1.  A maintainer must address any concerns left in the comments section
2.  A maintainer must check that all tests pass in the jenkins environment
3.  A maintainer must test the changes on his local machine and make sure that

all tests pass using the <span class="underline">plugin</span> *indy<sub>pool</sub>*

