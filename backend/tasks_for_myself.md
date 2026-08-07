backend: python and fastapi 
api: connect poke api with a DB and maybe 2 seperate DB's depending if i can not combine the right weaknesses and strenghts of pokemon to their respective id and combine the pokemon api get call with the weaknesses and strenghts api call
done, seeded DB with pokemon and strengths/weaknesses

check code for errors
prelimary check and fixes complete, need to run check again


build for post and delete a seperate api and connect both 
connection done fix error that db2 cannot be loaded when both instances are running and the weboverlay is active



as of right now not possible, error with creating 2nd db and sqlalchemy currently not working in venv
fix error in correspondence to error report, fix DB limit and naming scheme

fixed both, db2 created, sqlalchemy imported into backend, in future check both .venv if dependencies are presenst


build DB with searchbar and have the DB restricted to 6 slots for current team and display alongside strengths and weknesses 

reworked code to add errorhandeling to api enpoint, to database and to seeding procedure and deleted obsolete code snippets associated with old code

build 2nd db searchbar has been added, altho 2nd db cannot be innitialized, might be bc of missing data inside the cells of the table. searching database does not yield results, need to investigate the connection

build a kind of pokedex searchable by name via searchbar
frontend: react with vite and javascript
connect both api´s to react and build a page to house it all if needed use multiple links to multiple subsites for better ui clarity and no overloading


saving to 2nd db fixed, writing and deleting to 2nd db as well as the max enty cap verified, naming scheme normalized and verified functionality. 

all in all: most functions now verifiable working and i think this is ready to send in. 

task for next week (10.08.2026) containerize application via docker to help with compatability. 
improve visuals in weboverlay (coloration is kinda trash, gotta rework it entirely and maybe add a background image to it.)
