/*************************************** 
Waveshare AlphaBot Car mjpg-AlphaBot

Command Line:
-----------------------------------------------------------------------------------------------------
{"Car":"Forward"}
{"Car":"Backward"}
{"Car":"Left"}
{"Car":"Right"}

Expended Command
{"Car":"Forward","Time":"1000"}   ------   Car run forward 1000ms
{"Car":"SetSpeed","Value":[250,200]} ------  Set speed as 250 on left motor and 200 on right motor
-----------------------------------------------------------------------------------------------------
{"LCD":"Display","Line1":"Waveshare","Line2":"Waveshare"}

CN: www.waveshare.net/wiki/AlphaBot
EN: www.waveshare.com/wiki/AlphaBot
****************************************/
#include "AlphaBot.h"
#include "ArduinoJson.h"
#include<Servo.h>

#define START '{'
#define END '}'

#define ENCODER_LEFT  2
#define ENCODER_RIGHT 3

bool Started = false;
bool Ended = false;

AlphaBot Car1 = AlphaBot();
Servo servo1;
Servo servo2;

//variables for the ENCODER_LEFT
unsigned int rpmLeft;     // rpm reading
volatile byte pulsesLeft;           // number of pulses
unsigned int rpmRight;     // rpm reading 
volatile byte pulsesRight;           // number of pulses
unsigned long timeold; 
unsigned int pulsesperturn = 20;// The number of pulses per revolution


char inData[80];
byte Num;

void encoderCounterLeft()
{
  pulsesLeft++;
}

void encoderCounterRight()
{
  pulsesRight++;
}

void updateEncoder()
{
  if (millis() - timeold >= 1000){  /*Uptade every one second, this will be equal to reading frecuency (Hz).*/
 
  //Don't process interrupts during calculations
   detachInterrupt(digitalPinToInterrupt(ENCODER_LEFT));
   detachInterrupt(digitalPinToInterrupt(ENCODER_RIGHT));
   //Note that this would be 60*1000/(millis() - timeold)*pulses if the interrupt
   //happened once per revolution
   rpmLeft = (60 * 1000 / pulsesperturn )/ (millis() - timeold)* pulsesLeft;
   rpmRight = (60 * 1000 / pulsesperturn )/ (millis() - timeold)* pulsesRight;
   timeold = millis();
   pulsesLeft = 0;
   pulsesRight = 0;
   
   //Write it out to serial port
   Serial.print("RPM left = ");
   Serial.println(rpmLeft,DEC);
   Serial.print("RPM right = ");
   Serial.println(rpmRight,DEC);
   Serial.println("-------------------");
   //Restart the interrupt processing
   attachInterrupt(digitalPinToInterrupt(ENCODER_LEFT), encoderCounterLeft, CHANGE);
   attachInterrupt(digitalPinToInterrupt(ENCODER_RIGHT), encoderCounterRight, CHANGE);
   }
}

void setup()
{
  Serial.begin(115200);
  Serial.println("start!");
  servo1.attach(9);
  servo2.attach(10);
  servo1.write(90);
  servo1.write(90);
  pinMode(ENCODER_LEFT, INPUT_PULLUP);
  pinMode(ENCODER_RIGHT, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(ENCODER_LEFT), encoderCounterLeft, CHANGE);
  attachInterrupt(digitalPinToInterrupt(ENCODER_RIGHT), encoderCounterRight, CHANGE);
  pulsesLeft = 0;
  rpmLeft = 0;
  pulsesRight = 0;
  rpmRight = 0;
  timeold = 0;
}

void loop()
{ 
  updateEncoder();
  while(Serial.available() > 0)
 {
   char ch = Serial.read();
   if(ch == START)
   {
     Num = 0;
     inData[Num++] = ch;
     Started = true;
     Ended = false;
   }else if(ch == END)
   {
     inData[Num++] = ch;
     inData[Num] = '\0';
     Ended = true;
   }else if(Started && !Ended)
   {
     inData[Num++] = ch;
   }else
   {
     inData[Num++] = ch;
   }
  }
  
   if(Started && Ended)
   {
     StaticJsonBuffer<80> jsonBuffer;
     JsonObject& DecodeData = jsonBuffer.parseObject(inData);
     
     if (!DecodeData.success())
    {
      Serial.println("parseObject() failed");
      Started = false;
      Ended = false;
      return;
    }
    
    const char* Car = DecodeData["Car"];
    const char* SERVO = DecodeData["Servo"];
    
    if(Car)
    {
      if(strcmp(Car,"Forward") == 0)         //{"Car":"Forward"}
        Car1.Forward();
      else if(strcmp(Car,"Backward") == 0)   //{"Car":"Backward"}
        Car1.Backward();
      else if(strcmp(Car,"Left") == 0)       //{"Car":"Left"}
        Car1.Left();
      else if(strcmp(Car,"Right") == 0)      //{"Car":"Right"}
        Car1.Right();
      else if(strcmp(Car,"SetSpeed") == 0)   //{"Car":"SetSpeed","Value":[250,200]}
      {
        byte LSpeed = DecodeData["Value"][0];
        byte RSpeed = DecodeData["Value"][1];
        Serial.println("SPEED");
        Serial.println(LSpeed);
        Serial.println(LSpeed);
        Car1.SetSpeed(LSpeed,RSpeed);
      }
      else
        Car1.Brake();
      
      unsigned int Time = DecodeData["Time"];
      if(Time > 0)
      {
        delay(Time);
        Car1.Brake();
      }
    }
    else if (SERVO)     //{"Servo:"Servo1","Angle":180}  {"Servo":"Servo1","Angle":180}
    {
      byte Angle;
      if(strcmp(SERVO,"Servo1") == 0)
      {
        Angle = DecodeData["Angle"]; 
        if(Angle)
        {
          servo1.write(180 - Angle);
        }
      }
      else if(strcmp(SERVO,"Servo2") == 0)
      {
         Angle = DecodeData["Angle"]; 
        if(Angle)
        {
          servo2.write(Angle);
        }
      }
    }
    
    Started = false;
    Ended = false;
   }
}
