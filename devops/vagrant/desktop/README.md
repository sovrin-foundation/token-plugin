# Vagrant Ubuntu Desktop with Pycharm
Intended for developers on Plenum Plugins https://github.com/evernym/plugin

## Requirements

Install VirtualBox. https://www.virtualbox.org/wiki/Downloads

Install vagrant.  https://www.vagrantup.com/downloads.html

Download Pycharm for ubuntu as .tar.gz file.  Put the file in
the common sub-directory and name the file pycharm-community.tar.gz.  *FAILURE
to follow this command will lead to errors.*

Additional vagrant documentation
https://www.vagrantup.com/docs/cli/
https://www.taniarascia.com/what-are-vagrant-and-virtualbox-and-how-do-i-use-them/


## Creating the vagrant image
1. In the same folder as the Vagrant file, run the command 'vagrant up'
2. Wait until the script is completely finished
3. In Virtual Box window, log in
    user: vagrant
    password: vagrant


## After log in:
1. shutdown the virtual environment.  from terminal run 'shutdown now'
2. In virtualbox manager, select 'sandbox-development' machine and
    2a change display memory to 16MB
    2b turn off remote display
3. Start Virtual machine by either
    3a double click in virtualbox manager -- or --
    3b call 'vagrant reload' from the same directory as the vagrant file

4. After log in, adjust display settings to something like 1400x1050
5. use git to get code (eg from https://github.com/evernym/plugin or whatever)

## Notes
Pycharm is in /home/vagrant/pycharm. To run Pycharm open a terminal and
cd to /home/vagrant/pycharm/bin.   run ./pycharm.sh
