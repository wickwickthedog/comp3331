import java.io.*;
import java.net.*;
import java.util.*;

/*
 * Server to process ping requests over UDP. 
 * The server sits in an infinite loop listening for incoming UDP packets. 
 * When a packet comes in, the server simply sends the encapsulated data back to the client.
 */

public class PingClient
{
   private static final int TIME_OUT = 1000;  // milliseconds

   public static void main(String[] args) throws Exception
   {
      // Get command line argument.
      if (args.length != 2) {
         System.out.println("Required arguments: host and port");
         return;
      }
      int port = Integer.parseInt(args[1]);
      // host
      InetAddress host = InetAddress.getByName(args[0]);

      // Create random number generator for use in simulating 
      // packet loss and network delay.
      Random random = new Random();

      // Create a datagram socket for receiving and sending UDP packets
      // through the port specified on the command line.
      DatagramSocket socket = new DatagramSocket();

      // socket timeout 1000ms
      socket.setSoTimeout(TIME_OUT);

      ArrayList<Long> rtts = new ArrayList<Long>();

      // Processing loop.
      for (int i = 0; i < 10; i++) {
         // start ping time
         long timeStart = System.currentTimeMillis();
         /*
          * \r = CR (Carriage Return) → Used as a new line character in Mac OS before X
          * \n = LF (Line Feed) → Used as a new line character in Unix/Mac OS X
          * \r\n = CR + LF → Used as a new line character in Windows
          */
         String message = "PING " + i + " " + timeStart + "\r\n";

         DatagramPacket request = new DatagramPacket(message.getBytes(), message.length(), host, port);
         // sent the packet
         socket.send(request);

         try {
            // Create a datagram packet to hold incomming UDP packet.
            DatagramPacket response = new DatagramPacket(new byte[1024], 1024);

            // Block until the host receives a UDP packet.
            socket.receive(response);

            long timeFinish = System.currentTimeMillis();

            rtts.add(timeFinish - timeStart);

            System.out.println("ping to " + host + ", seq = " + i + ", rtt = " + (timeFinish - timeStart) + "ms");
         } catch (SocketTimeoutException e) {
            System.out.println("ping to " + host + ", seq = " + i + ", TIME OUT");
         }
      }
      // You will also need to report the minimum, maximum and the average RTTs of all packets received successfully 
      // at the end of your program's output.
      long min = Collections.min(rtts);
      long max = Collections.max(rtts);
      long average = 0;
      for (long rtt : rtts) {
         average += rtt;
      }
      average /= rtts.size();

      System.out.println("----- Report -----");
      System.out.println("The minimum rtt = " + min + "ms");
      System.out.println("The maximum rtt = " + max + "ms");
      System.out.println("The average rtt = " + average + "ms");
   }

   /* 
    * Print ping data to the standard output stream.
    */
   private static void printData(DatagramPacket request) throws Exception
   {
      // Obtain references to the packet's array of bytes.
      byte[] buf = request.getData();

      // Wrap the bytes in a byte array input stream,
      // so that you can read the data as a stream of bytes.
      ByteArrayInputStream bais = new ByteArrayInputStream(buf);

      // Wrap the byte array output stream in an input stream reader,
      // so you can read the data as a stream of characters.
      InputStreamReader isr = new InputStreamReader(bais);

      // Wrap the input stream reader in a bufferred reader,
      // so you can read the character data a line at a time.
      // (A line is a sequence of chars terminated by any combination of \r and \n.) 
      BufferedReader br = new BufferedReader(isr);

      // The message data is contained in a single line, so read this line.
      String line = br.readLine();

      // Print host address and data received from it.
      System.out.println(
         "Received from " + 
         request.getAddress().getHostAddress() + 
         ": " +
         new String(line) );
   }
}
