export MAKE=/usr/bin/make

red=`tput setaf 1`
green=`tput setaf 2`
echo "${red}BEGIN BUILDING: ${green}sovtoken.deb "
eval "SRC_DIR_NAME=sovtoken make -C devops/ package_in_docker" > /dev/null
echo "${red}BEGIN BUILDING: ${green}sovtokenfees.deb "
eval "SRC_DIR_NAME=sovtokenfees make -C devops/ package_in_docker" > /dev/null
echo "${red}MOVING: ${green}sovtoken.deb "
mv devops/_build/sovtoken/*.deb devops/build-scripts/xenial/Pool_Party/.
echo "${red}MOVING: ${green}sovtoken.deb "
mv devops/_build/sovtokenfees/*.deb devops/build-scripts/xenial/Pool_Party/.

cd devops/build-scripts/xenial/Pool_Party/
echo "${red}BUILD: ${green} payment ledger"
docker build -t indy_pool . > /dev/null
echo "${red}RUNNING: ${green} payment ledger"
docker run -itd -p 9701-9708:9701-9708 indy_pool > /dev/null
echo "${red}Payment Ledger Success: ${green} payment ledger"
