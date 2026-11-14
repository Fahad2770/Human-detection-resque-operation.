#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>

// Apne Mobile Hotspot ya Home Wi-Fi ka naam aur password yahan likhein
const char* ssid = "YOUR_WIFI_OR_HOTSPOT_NAME";
const char* password = "YOUR_WIFI_PASSWORD";

// ThingSpeak ya kisi bhi Public Cloud API ka link (Jahan data bheજના hai)
const String serverName = "http://api.thingspeak.com/update?api_key=YOUR_API_KEY&field1=";

void setup() {
  Serial.begin(115200);
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  
  Serial.print("Connecting to Wi-Fi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected to Wi-Fi!");
}

void loop() {
  if(WiFi.status() == WL_CONNECTED){
    int rssi = WiFi.RSSI(); // Wi-Fi signal strength naapنا
    
    HTTPClient http;
    String serverPath = serverName + String(rssi);
    
    http.begin(serverPath.c_str());
    int httpResponseCode = http.GET();
    
    if (httpResponseCode > 0) {
      Serial.print("Data sent successfully. RSSI: ");
      Serial.println(rssi);
    } else {
      Serial.print("Error sending data: ");
      Serial.println(httpResponseCode);
    }
    http.end();
  }
  
  delay(3000); // Har 3 second baad naya data bheje ga
}
