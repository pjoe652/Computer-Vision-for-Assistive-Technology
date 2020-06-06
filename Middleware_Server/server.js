const express = require('express')
const cors = require('cors')
const bodyParser = require('body-parser')
const knex = require('knex')

const db = knex({
	client: 'pg',  
	connection: process.env.DATABASE_URL
}) 

/* Intialize the database */
const initializeDatabase = () => {
    db.schema.hasTable("Hosts").then(function(exists){
        if(!exists) {
            console.log("Creating Host table")
            return db.schema.createTable("Hosts", function(t) {
                t.string("user");
                t.string("url");
                t.string("type");
                console.log("Created Host table")
            })
        } else {
            console.log("Table already exists")
        }
    })
}

initializeDatabase();

const app = express()
app.use(bodyParser.json())
app.use(cors())

/* Logs server type in database */
app.post('/log', (req, res) => {
    const { user, url, type } = req.body;

    if(!user || !url || !type) {
        console.log(req.body)
        return res.status(400).json("Incorrect parameters")
    }

    if(type !== "server" && type !== "camera") {
        console.log(req.body)
        return res.status(400).json("Only Camera and Servers are allowed as types")
    }

    db("Hosts").insert({
        user: user.toUpperCase(),
        url: url,
        type: type
    })
    .then(result => {
        console.log("Added host")
        res.status(200).json("Host added")
    })
})

/* Remove recognition server from the database */
app.get('/clearServer', (req, res) => {

    const { username } = req.query

    if(!username) {
        console.log(req.body)
        return res.status(200).json("Invalid request")
    }
    
    db("Hosts")
    .where({ user: username,
             type : "server" })
    .del()
    .then(data => {
        res.status(200).json("Deleted server");
    })
})

/* Remove raspberry pi server from the database */
app.get('/clearCamera', (req, res) => {
    const { username } = req.query

    if(!username) {
        return res.status(200).json("Invalid request")
    }
    
    db("Hosts")
    .where({ user: username,
             type : "camera" })
    .del()
    .then(data => {
        res.status(200).json("Deleted camera");
    })
})

/* Get all servers stored in the database */
app.get('/allLogs', (req, res) => {
    db.select('*').from("Hosts")
    .then(data => {
        res.status(200).json(data)
    })
    .catch(err => {
        res.status(400).json("Something went wrong with the database")
    })
})

/* Get the recognition server from the database */
app.get('/host', (req, res) => {
    db.select('*').from("Hosts")
    .where('type', '=', 'server')
    .then(data => {
        res.status(200).json(data);
    })
    .catch(err => {
        res.status(400).json("No host on the server");
    })
})

app.get('/', (req, res) => {
    res.status(200).json("Hello world! v1")
})

app.listen((process.env.PORT || 5000), () => {
    console.log("App is running")
})