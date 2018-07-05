MAKE=/usr/bin/make
SRC_DIR_NAME=sovtoken make -C devops/ package_in_docker sovtoken 
SRC_DIR_NAME=sovtokenfees make -C devops/ package_in_docker sovtokenfees

mv devops/_build/sovtoken/*.deb devops/build-scripts/xenial/Pool_Party/.
mv devops/_build/sovtokenfees/*.deb devops/build-scripts/xenial/Pool_Party/.

cd devops/build-scripts/xenial/Pool_Party/
docker build -t indy_pool .

docker run -itd -p 9701-9708:9701-9708 indy_pool
