export MAKE=/usr/bin/make

red=`tput setaf 1`
green=`tput setaf 2`
reset=`tput sgr0`
printf "\n${red}BEGIN BUILDING:\t${green}sovtoken.deb\n"
sov_token=$(eval "SRC_DIR_NAME=sovtoken make -C devops/ package_in_docker" 2> /dev/null)
printf "${reset}SUCCESS:\t${green}sovtoken.deb built\n\n"

printf "${red}BEGIN BUILDING:\t${green}sovtokenfees.deb\n"
sov_token_fees=$(eval "SRC_DIR_NAME=sovtokenfees make -C devops/ package_in_docker" 2> /dev/null)
printf "${reset}SUCCESS:\t${green}sovtokenfees.deb built\n\n"


printf "${red}MOVING: ${green}sovtoken.deb to devops/build-scripts/xenial/Pool_Party/\n"
mv devops/_build/sovtoken/*.deb devops/build-scripts/xenial/Pool_Party/.

printf "${red}MOVING: ${green}sovtoken.deb to devops/build-scripts/xenial/Pool_Party/\n"
mv devops/_build/sovtokenfees/*.deb devops/build-scripts/xenial/Pool_Party/.

printf "\n${reset}FILES HAVE BEEN MOVED SUCCESSFULLY\n"

cd devops/build-scripts/xenial/Pool_Party/
printf "\n${red}BEGIN BUILDING:${green} payment ledger${reset}\nPlease Be Patient RocksDB and the Payment Ledger are being built\n\n"
docker build -t indy_pool . > /dev/null  & PID=$!
printf "["
while kill -0 $PID 2> /dev/null; do 
    printf  "▓"
    sleep 1
done
printf "]\n\nBUILD COMPLETE\n\n"
printf "${red}RUNNING:\t${green} payment ledger\n"
docker run -itd -p 9701-9708:9701-9708 indy_pool > /dev/null
printf "${green}Success:\t${reset} payment ledger is now ready to use\n"
