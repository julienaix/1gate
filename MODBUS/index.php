<html xmlns = "http://www.w3.org/1999/xhtml" xml:lang="fr" lang="fr">

	<head>
 		<title>1gate configurator</title>
		<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1"/>
		<link href="style.css?v1" rel="stylesheet" type="text/css"/>
	</head>

	<body>

        <div class="header">
        
		<p><a href="index.php"><img src="img/atim.png" alt="ATIM"></a></p>

		<h1>1gate configurator</h1>

		<div class ="version">
			<br />
			<?php
				//Modbus srevice version
                        	$modbusVersion = file_get_contents('/var/www/html/modbus.version');
                        	echo "Modbus service version $modbusVersion";
                        	echo("<br /><br />");

                        	//Chirpstack Version
                        	$chirpstackVersion = shell_exec('chirpstack-gateway-bridge version');
                        	echo "Chirpstack version $chirpstackVersion";

			?>
		</div>

        </div>

	<ul class = "menu">

 		<li><a href="#menu1">LAN</a></li>
		<li class = "separator"></li>
  		<li></div><a href="#menu2">LORA</a></li>
		<li class = "separator"></li>
  		<li><a href="#menu4">MODBUS</a></li>
	</ul>

	<br />

	<div class="body">

		<!--------------------------------------------------------------------------------------------------------------------------------->
                <!--MENU 1 : LAN CONFIGURATION ---------------------------------------------------------------------------------------------------->
		<!--------------------------------------------------------------------------------------------------------------------------------->

		<div id="menu1">
		<form method="post" action="process1.php" enctype="multipart/form-data">
		<?php		       
		//1. Check Ethernet connection

		//1.1 Check if ethernet peripheral is active
		$content=shell_exec('ifconfig eth0');
                //Parse lines
		$lines = explode("\n", $content);
		//echo($lines[1]);
                if(strpos($lines[1],"inet") != false)
		{
			$ethernet = 1;
			//Get IP addresses
                        $ips = preg_split('/\s+/', $lines[1]);
					
		}
		else $ethernet = 0;

		//1.2 Check if static adressing is active
                //Files path to be checked
                $dhcpFile='/etc/dhcpcd.conf';

               	//Open the files to be checked( connection status and configuration)
              	$dhcpContent = file_get_contents($dhcpFile);

               	//parse the lines 
                $dhcpLines = explode("\n", $dhcpContent);
				
		if(strpos($dhcpLines[40],"eth0") != false)
		{
			$static = 1;			
		}

		else $static = 0;
			
        	?>
		<h2>Ethernet :</h2>
                <?php
		//If ethernet connection is active display current IP address
                if($ethernet == 1)
                {
                        echo "Current IP : $ips[2]";
                        echo("<br /><br />");
                }

		//Display ethernet button according to configuration 

                if($static == 1)
                {
                ?>

                	<label class="container"> DHCP
                        	<input type="radio" name="ethernet" value ="dhcp">
                                <span class="checkmark"></span>
                         </label>

                        <label class="container"> STATIC
                        	<input type="radio" name="ethernet" value ="static" checked="checked">
                                <span class="checkmark"></span>
                        </label>

                <br /><br />

		<?php
                }

                else
                {
                ?>

                        <label class="container"> DHCP
                                <input type="radio" name="ethernet" value ="dhcp" checked="checked">
                                <span class="checkmark"></span>
                        </label>

                        <label class="container"> STATIC
                                <input type="radio" name="ethernet" value ="static">
                                <span class="checkmark"></span>
                        </label>

                <br /><br />

                <?php
                }
		?>
		<label for="ethIP">Static IP address:</label><br>
                <label class="text_field">
                	<input type="text" id="ethIP"  name="ethIP" size="12"/>
			/
			<input type="text" id="ethMASK"  name="ethMASK" size="1"/>
                </label>
                <br /><br />

		<label for="ethGW">Gateway IP address:</label><br>
                <label class="text_field">
                <input type="text" id="ethGW"  name="ethGW"size="12"/>
                </label>
                <br /><br />



		<?php
			
		//2.Check wifi connection
	        //2.1 Check if wifi peripheral is active
                $content=shell_exec('ifconfig wlan0');
                //Parse lines
                $lines = explode("\n", $content);
                //echo($lines[1]);
                if(strpos($lines[1],"inet") != false)
                {
	                $wifi = 1;
	                //echo("test1");
                }
                else $wifi = 0;

                //Get IP address
                $ips = preg_split('/\s+/', $lines[1]);
                //echo "IP address :$ips[2]";

                //2.2 Check if static adressing is active
                //Files path to be checked
                $dhcpFile='/etc/dhcpcd.conf';

                //Open the files to be checked( connection status and configuration)
                $dhcpContent = file_get_contents($dhcpFile);

                //parse the lines
                $dhcpLines = explode("\n", $dhcpContent);
                //echo($dhcpLines[40]);
                if(strpos($dhcpLines[40],"wlan0") != false)
                {
                	$staticWifi = 1;
                        //echo("test2");
		}
		else $staticWifi = 0;
                ?>
                
                <h2>WIFI :</h2>
                <?php

                if($wifi == 1)
                {
	                echo "Current IP :$ips[2]";
                        echo("<br /><br />");
                }

                //Display WIFI button according to configuration 
                if($wifi == 0)
                {
                ?>

                	<label class="container"> DHCP
                        	<input type="radio" name="wifi" value ="dhcp">
                                <span class="checkmark"></span>
                        </label>

                        <label class="container"> STATIC
                        	<input type="radio" name="wifi" value ="static">
                                <span class="checkmark"></span>
                        </label>

                        <label class="container"> OFF
                                <input type="radio" name="wifi" value ="off" checked="checked">
                                <span class="checkmark"></span>
                        </label>

                        <br /><br />
                <?php
                }

                else if($wifi == 1 && $staticWifi == 1)
                {
                ?>

                                <label class="container"> DHCP
                                        <input type="radio" name="wifi" value ="dhcp">
                                        <span class="checkmark"></span>
                                </label>

                                <label class="container"> STATIC
                                        <input type="radio" name="wifi" value ="static" checked="checked">
                                        <span class="checkmark"></span>
                                </label>

                                <label class="container"> OFF
                                        <input type="radio" name="wifi" value ="off">
                                        <span class="checkmark"></span>
                                </label>

                                <br /><br />
                <?php
                }

                else if($wifi == 1 && $staticWifi == 0)
                {
                ?>

                                <label class="container"> DHCP
                                        <input type="radio" name="wifi" value ="dhcp" checked="checked">
                                        <span class="checkmark"></span>
                                </label>

                                <label class="container"> STATIC
                                        <input type="radio" name="wifi" value ="static">
                                        <span class="checkmark"></span>
                                </label>

                                <label class="container"> OFF
                                        <input type="radio" name="wifi" value ="off">
                                        <span class="checkmark"></span>
                                </label>

                                <br /><br />
                <?php
                }

                ?>
                        <label for="wlanIP">Static IP address:</label><br>
                        <label class="text_field">
                        	<input type="text" id="wlanIP"  name="wlanIP"size="12"/>
                                / 
                                <input type="text" id="wlanMASK"  name="wlanMASK" size="1"/>

                        </label>
			<br /><br />

                        <label for="wlanGW">Gateway IP address:</label><br>
                        <label class="text_field">
                                <input type="text" id="wlanGW"  name="wlanGW"size="12"/>
                        </label>
                        <br /><br />


			<label>Register WIFI network :</label><br>

			<label class="indication"> SSID </label>
			<label class="text_field">
                        	<input type="text" name="ssid"size="20"/>
                        </label>
			<br />

                        <label class="indication"> Password </label> 
                        <label class="text_field">
	                        <input type="password" name="password"size="20"/>
                        </label>

			<br /><br />
			

		<input type="submit" value="OK"/>
        	<br />

		</form>     

		</div> <!-- End of menu1-->

		<!--------------------------------------------------------------------------------------------------------------------------------->
                <!--MENU 2 : LORA/CHIRPSTACK CONFIGURATION ---------------------------------------------------------------------------------------->
		<!--------------------------------------------------------------------------------------------------------------------------------->

		<div id="menu2">
			
			<form method="post" action="process2.php" enctype="multipart/form-data">
			
			<p>
                        Import device list :<br />
                                <label class="text_field">
                                	<input type="file" name="devlist" />
                                </label>
                        </p>


			<input type="submit" value="OK"/>
                	<br />

                	</form>     


		</div> <!-- End of menu2-->

                <!--------------------------------------------------------------------------------------------------------------------------------->
		<!--MENU 4 : MODBUS CONFIGURATION ------------------------------------------------------------------------------------------------->
		<!--------------------------------------------------------------------------------------------------------------------------------->


		<div id="menu4">

			<?php
			//Copy the log file
                        shell_exec("cp /home/ogate/MODBUS/modbus.log /var/www/html");

			?>
			<a href="modbus.log">
  			Download logs
			</a>
 			<br /><br />
			<?php

			//Files path to be checked
			$devicesFile='/home/ogate/MODBUS/modbus.dev';
			
			//Open the files to be checked( connection status and configuration)
			$devicesContent = file_get_contents($devicesFile);
			
			//parse the files
			$devicesLines = explode("\n", $devicesContent);
			$devicesCnt = count($devicesLines);
			
                        //MODBUS adress start from 100
                        $adr = 0;

			if($devicesCnt > 1)
			{
                        //Display MODBUS devices address tab
                        for ($i = 0; $i < $devicesCnt-1; $i++)
			{
			//Parse the line
			$devicesElements = explode(",", $devicesLines[$i]);
			//Split the bytes from MODBUS payload
			$devicesBytes = str_split($devicesElements[1],4);
			//Print devEUI
			?> <strong> devEUI:</strong><?php
			print $devicesElements[0];
			
			//Split time stamp
			//$devicesTime = str_split($devicesElements[2],1);
			
			?> <strong>  Last seen: </strong><?php
			//print "$devicesTime[6]$devicesTime[7]/$devicesTime[4]$devicesTime[5]/$devicesTime[0]$devicesTime[1]$devicesTime[2]$devicesTime[3] $devicesTime[8]$devicesTime[9]:$devicesTime[10]$devicesTime[11]:$devicesTime[12]$devicesTime[13]";
			print $devicesElements[2];
			?>      
				<br /><br />

				<table>
					<tr>
                                                <?php
						//
                                         	for ($j = 0; $j < 25; $j++) 
                                                {
						$adr = $adr + 1;
                                                ?>
                                                        <td>
                                                        <?php 
							print $adr;
							?> 
                                                        </td>
                                                        <?php
                                                }
                                                ?>
					</tr>

					<tr>
                                                <?php
                                                for ($j = 0; $j < 25; $j++) 
                                                {
                                                
                                                ?>
                                                        <td>
                                                        <?php print $devicesBytes[$j];?> 
                                                        </td>
                                                        <?php
                                                }
                                                ?>

					</tr>

				</table>
				<br />

                        <?php
                        }//End of for loop
			?>
                        <form method="post" action="process4.php" enctype="multipart/form-data">

                        <input type="submit" value="RESET"/>
                        <br />

                        </form>     
			
			<?php
			}//End of if

			else echo "Device table is empty";
			?>

		</div><!-- End of menu4-->


	</div><!-- End of body-->

        <div class="footer">
        	<p>Need help? Visit <a href="https://www.atim.com/en/technical-support/"> www.atim.com/en/technical-support</a></p>
        	<p><a href=update.php> Update Gateway </a></p>
	</div>

    </body>
</html>
