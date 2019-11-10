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

//ISR for encoder intrrupt
void encoderCounterLeft(){pulsesLeft++;}

void encoderCounterRight(){pulsesRight++;}



void setup()
{
  Serial.begin(115200);
  Serial.println("start!");
  
  //start servo setup
  servo1.attach(9);   //base servo
  servo2.attach(10);  //head 
  //stop servo setup

  //start encoder setup
  pinMode(ENCODER_LEFT, INPUT_PULLUP);
  pinMode(ENCODER_RIGHT, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(ENCODER_LEFT), encoderCounterLeft, CHANGE);
  attachInterrupt(digitalPinToInterrupt(ENCODER_RIGHT), encoderCounterRight, CHANGE);
  pulsesLeft = 0;
  rpmLeft = 0;
  pulsesRight = 0;
  rpmRight = 0;
  timeold = 0;
  //stop encoder setup

  //setting initial servo value
  servo1.write(90);
  servo2.write(80);

  //set car spped
  byte initSpeed = 200;
  Car1.SetSpeed(initSpeed,initSpeed);

}

void loop()
{ 
  //updateEncoder();
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
      //turning left, this will rotate left wheel so read right encoder values
      else if(strcmp(Car,"Left") == 0)       //{"Car":"Left"}
        {
          long turnAngle = DecodeData["Value"][0];
          attachInterrupt(digitalPinToInterrupt(ENCODER_RIGHT), encoderCounterRight, CHANGE);
          Car1.Left();
          long tempCounter = 0;
          while (tempCounter<=turnAngle)
          {
            detachInterrupt(digitalPinToInterrupt(ENCODER_RIGHT));
            tempCounter = pulsesRight;
            attachInterrupt(digitalPinToInterrupt(ENCODER_RIGHT), encoderCounterRight, CHANGE);
            
          }
          
          Car1.Brake();
          detachInterrupt(digitalPinToInterrupt(ENCODER_RIGHT));
          pulsesRight = 0;
        }
      //turning Right, this will rotate left wheel so read left encoder values
      else if(strcmp(Car,"Right") == 0)      //{"Car":"Right"}
        {
          long turnAngle = DecodeData["Value"][0];
          attachInterrupt(digitalPinToInterrupt(ENCODER_LEFT), encoderCounterLeft, CHANGE);
          long tempCounter = 0;
          pulsesLeft = 0;
          Car1.Right();
          while (tempCounter<=turnAngle)
          {
            detachInterrupt(digitalPinToInterrupt(ENCODER_LEFT));
            tempCounter = pulsesLeft;
            attachInterrupt(digitalPinToInterrupt(ENCODER_LEFT), encoderCounterLeft, CHANGE);
            
          }
          
          Car1.Brake();
          detachInterrupt(digitalPinToInterrupt(ENCODER_LEFT));
          pulsesLeft = 0;
        }
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
