let socket;


let username = sessionStorage.getItem(
    "meetingUsername"
);

if (!username) {

    username = prompt("Enter your name:");

    if (!username) {

        username = "Guest";

    }

    sessionStorage.setItem(
        "meetingUsername",
        username
    );

}


// Create WebSocket connection

socket = new WebSocket("ws://127.0.0.1:8000/ws");


// When connection opens

socket.onopen = function () {

    console.log("Connected to meeting server");

    // Send username to backend

    socket.send(username);

};


// Receive message

socket.onmessage = function (event) {

    const data = JSON.parse(event.data);

    console.log(data);


    // User joined

    if (data.type === "join") {

        addMessage(
            "System",
            data.message
        );

        updateOnlineUsers(
            data.online_users
        );

    }
    else if (data.type === "ai_suggestion") {

    showAISuggestion(
        data.suggestion,
        data.topic
    );

}


    // Normal message

    else if (data.type === "message") {

        addMessage(
            data.username,
            data.message
        );

    }


    // User left

    else if (data.type === "leave") {

        addMessage(
            "System",
            data.message
        );

        updateOnlineUsers(
            data.online_users
        );

    }

};


// Add message to transcript

function addMessage(username, message) {

    const messages =
        document.getElementById("messages");


    const messageDiv =
        document.createElement("div");


    messageDiv.className = "message";


    messageDiv.innerHTML = `
        <strong>${username}:</strong>
        <p>${message}</p>
    `;


    messages.appendChild(messageDiv);


    // Scroll to latest message

    messages.scrollTop =
        messages.scrollHeight;

}


// Update online users

function updateOnlineUsers(count) {

    document.getElementById(
        "onlineCount"
    ).innerText = `${count} Online`;

}


// Send message

function sendMessage() {

    const input =
        document.getElementById("messageInput");


    const message =
        input.value.trim();


    if (message === "") {

        return;

    }


    if (socket.readyState === WebSocket.OPEN) {

        socket.send(message);

        input.value = "";

    }

}


// Leave meeting

function leaveMeeting() {

    if (socket) {

        socket.close();

    }

    window.location.href = "index.html";

}


function showAISuggestion(suggestion, topic) {

    document.getElementById(
        "aiSuggestion"
    ).innerText = suggestion;


    document.getElementById(
        "topic"
    ).innerText = topic;

}


// Speech Recognition

const SpeechRecognition =
    window.SpeechRecognition ||
    window.webkitSpeechRecognition;


let recognition;


if (SpeechRecognition) {

    recognition = new SpeechRecognition();

    recognition.continuous = false;

    recognition.interimResults = false;

    recognition.lang = "en-US";


    recognition.onresult = function(event) {

        const transcript =
            event.results[0][0].transcript;


        document.getElementById(
            "messageInput"
        ).value = transcript;

    };


    recognition.onerror = function(event) {

        console.log(
            "Speech recognition error:",
            event.error
        );

    };

}


function startListening() {

    if (!recognition) {

        alert(
            "Speech recognition is not supported in this browser."
        );

        return;

    }


    recognition.start();

}



async function getSummary() {

    try {

        const response = await fetch(
            "http://127.0.0.1:8000/meeting/summary",
            {
                method: "POST"
            }
        );

        const data = await response.json();

        alert(data.summary);

    }

    catch (error) {

        console.log("Summary error:", error);

    }

}