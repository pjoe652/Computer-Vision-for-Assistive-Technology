const NodeWebcam = require( "node-webcam" );
const express = require("express");
const cors = require("cors");
const bodyParser = require("body-parser");
const ngrok = require("ngrok")
const fetch = require("node-fetch")
const Base64 = require("js-base64").Base64
const utf8 = require("utf8")



let globalUrl = "";
// Camera Options
const opts = {
    // saveShots: save,
    output: "jpeg",
    callbackReturn: "base64"
};

let capture;
let save = false;
/*
    ready - Determines whether the server is ready, if Ngrok is not necessary then keep as true otherwise set as false
    noHost - Determines whether the computational server is ready, if Ngrok is not necessary then change comp_server to the address of the recognition server and leave noHost as false 
    otherwise leave comp_server as blank
*/
let ready = true;
let noHost = false;
let comp_server;

const captureImage = () => {
    NodeWebcam.capture( "test_picture", opts, function( err, data ) {
        let image = data.replace("data:image/jpeg;base64,", "");
        store = "False";
        if(save) {
            store = "True"
        }
        fetch(`${comp_server}/identifyPose`, {
            method: "POST",
            body: JSON.stringify({
                img: image,
                store: store,
                username: "111"
            }),
            headers: {"Content-Type": "application/json"}
        }).catch(err => {
            console.log(err)
        })
    });
}

/* Set up a Ngrok server */
/* If you do not need Ngrok to portforward, this is not necessary, otherwise use an authtoken from Ngrok */
/*
async function getUrl(){
    const url = await ngrok.connect({authtoken: "", addr: 5000});
    fetch("https://p4-hoster.herokuapp.com/log", {
        method: "POST",
        body: JSON.stringify({
            user: "111",
            url: url,
            type: "camera"
        }),
        headers: { "Content-Type": "application/json"}
    })
    .then(res => res.json())
    .then(json => console.log(json));
    ready = true;
    console.log(url);
}

getUrl();
*/

// const checkServerAvailable = setInterval(checkServer, 5000)

// function checkServer(){
//     fetch("https://p4-hoster.herokuapp.com/host")
//     .then(res => res.json())
//     .then(json => {
//         if(json.length == 0) {
//             console.log("No available servers")
//             noHost = true;
//         } else {
//             console.log(json)
//             json.forEach(item => {
//                 if("111" == item.user) {
//                     comp_server = item.url
//                     noHost = false;
//                     console.log("Finished!")
//                     clearInterval(checkServerAvailable)
//                 }
//             })
//         }
//     })
//     .catch(e => {
//         console.log(e)
//     })
// }



/* Server API */
const app = express()
app.use(cors());
app.use(bodyParser.json());

/* Turns on the camera for the server */
app.get("/OnCamera", (req, res) => {
    if(noHost) {
        res.status(400).json("Computational server is not on")
    } else if(!ready) {
        res.status(400).json("Server has not finished setting up")
    } else {
        capture = setInterval(captureImage, 3000)
        res.status(200).json("Camera has been turned on")
    }
})

/* Turns off the camera for the server */
app.get("/OffCamera", (req, res) => {
    if(noHost) {
        res.status(400).json("Computational server is not on")
    } else if(!ready) {
        res.status(400).json("Server has not finished setting up")
    } else {
        clearInterval(capture)
        res.status(200).json("Camera has been turned off")
    }
})

/* Saves images */
app.get("/SaveImage", (req, res) => {
    save = true;
    res.status(200).json("Settings have been changed")
})

/* Does not save images */
app.get("/SendImage", (req, res) => {
    save = false;
    res.status(200).json("Settings have been changed")
})

app.listen((5000), () => {
    console.log("App is running")
})

process.stdin.resume();

process.on('SIGINT', code => {
    /* Remove camera from available cameras */
    fetch("https://p4-hoster.herokuapp.com/clearCamera?username=111")
    .then(res => res.json())
    .then(json => {
    })
    .catch(e => {
    })
})