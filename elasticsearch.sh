docker stop es-node01
docker rm es-node01
# docker run -d --name es-node01 -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" -e "xpack.security.enabled=false" docker.elastic.co/elasticsearch/elasticsearch:7.14.0

docker stop kib-01
docker rm kib-01
# docker run -d --name kib-01 -p 5601:5601 -e "ELASTICSEARCH_HOSTS=http://localhost:9200" docker.elastic.co/kibana/kibana:7.14.0
