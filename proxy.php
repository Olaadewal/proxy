
<?php
// Allow cross-origin requests
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET');

// Retrieve user input for the country and number of proxies

$numProxies = isset($_GET['numProxies']) ? (int)$_GET['numProxies'] : 1;

// Build the API URL with user input
$apiUrl = "http://192.168.170.219:10000/ip/numerous_bind?num=$numProxies&country=random&state=random&city=random&isp=random&zip=random&t=txt&port=6000";

// Fetch text data from the external API
$data = file_get_contents($apiUrl);

// Send the data as plain text response
header('Content-Type: text/plain');
echo $data;
