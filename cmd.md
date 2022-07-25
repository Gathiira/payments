# Elastic Search Commands

`docker swarm init`

`docker stack deploy -c docker-compose.elk.yml elk`

`docker exec -it <elasticsearch container id> bash`

`bin/elasticsearch-setup-passwords auto --batch --url http://elasticsearch:9200`

`docker stack rm elk`
