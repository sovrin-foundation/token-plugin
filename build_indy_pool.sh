export MAKE=/usr/bin/make
eval "SRC_DIR_NAME=sovtoken make -C devops/ package_in_docker"
eval "SRC_DIR_NAME=sovtokenfees make -C devops/ package_in_docker"

mv devops/_build/sovtoken/*.deb devops/build-scripts/xenial/Pool_Party/.
mv devops/_build/sovtokenfees/*.deb devops/build-scripts/xenial/Pool_Party/.

cd devops/build-scripts/xenial/Pool_Party/
docker build -t indy_pool .

docker run -itd -p 9701-9708:9701-9708 indy_pool
