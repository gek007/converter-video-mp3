## Converterter Video to mp3 -  microservice architecture

**This app should implements a microservice architectures where we will be applying this architecture to an application that will convert video files to MP3 files.** 

Let's go over what this application how it's going to look like from a top-down perspective. 

So when a user uploads a video to be converted to MP3 that request will first hit our Gateway. 

Our Gateway will then store the video in Mongodb and then put a message on this queue which is our RabbitMQ letting down stream services know that there's video to be processed in Mongodb.  

Video to MP3 converter will consume messages from the queue it will then get the idea of the video from the message deal to MP3 then store the MP3 on mongodb 

Then put a new message on the queue to be consumed by the notification service that says that the conversion job is done . The notification service consumes those messages from the queue and send an email notification to the client informing the client that the MP3 for the video that he or she uploaded is ready for download. 

The client will then use a unique ID requirement from the notification plus his or her JWT to make a request to the API Gateway to download the MP3 and the API Gateway will pull the MP3 from Mongodb and serve it to the client and that is the overall conversion flow and how RabbitMQ a is integrated with the overall system. 


=========================

MySQL DB
user: kshilrot@email 
pass: Admin123

==================

# you can locally rich rabbit in browser (if k8s is running) by:
# hosts file has config for it 

Username: admin
Password: guest

Access URLs:
http://localhost:15672 (port-forward)
http://rabbitmq-manager.com (ingress - add to hosts file)



