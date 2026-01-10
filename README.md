# TakeHomeGDV
Take home task for demonstration of technical skills.

notes for me for further work: Mac architecture means that I needed to find alternative solution for postgis
I am currently going with emulation, in the hope that Svet is using a non arm64 architecture CPU.

# notes for self
docker compose up -d db for db
docker compose down -v for testing,
docker compose logs db 
# when something doesn't work


docker compose exec db bash for entering docker
db name is mydatabase
user name is psql
we're looking for 
psql -U psql -d mydatabase

# more notes
on mac you're having to use private/tmp instead of just being able to access files.

you need to copy the csv into the docker container.

#readme section 1 how to connect to db commands