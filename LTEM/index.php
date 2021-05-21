<html xmlns = "http://www.w3.org/1999/xhtml" xml:lang="fr" lang="fr">

	<head>
 		<title>1gate configurator</title>
		<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1"/>
		<link href="style.css?v=3" rel="stylesheet" type="text/css"/>
	</head>

	<body>

        <div class="header">
        
		<p><a href="index.php"><img src="img/atim.png" alt="ATIM"></a></p>

		<h1>1gate configurator</h1>

		<div class ="version">
			<br />
			<?php
			$version = shell_exec('chirpstack-gateway-bridge version');
			echo "Chirpstack version $version";
			?>
		</div>

        </div>

	<ul class = "menu">

 		<li><a href="#menu1">LAN</a></li>
		<li class = "separator"></li>
  		<li></div><a href="#menu2">LORA</a></li>
		<li class = "separator"></li>
  		<li><a href="#menu3">LTEM</a></li>
	</ul>

	<br />

	<div class="body">

                <!--MENU 1 : LAN CONFIGURATION ---------------------------------------------------------------------------------------------------->
		<div id="menu1">

		<?php

			//1. Check if hotspot is on
                        $ifconfig=shell_exec('systemctl status hostapd');
                        //Parse lines
                        $lines = explode("\n", $ifconfig);

			echo "WIFI hotspot : ";

			if(strpos($lines[2],"running") != false)
			{
				?> <span class="ONstate">ON</span> <br /><br />  <?php
				$hotspot = 1;
			}
			else
			{
				?> <span class="OFFstate">OFF</span><br /><br />  <?php
				$hotspot = 0;
			}

			//2. Check if ethernet is on
			$ifconfig=shell_exec('ifconfig eth0');

                        //Parse lines
                        $lines = explode("\n", $ifconfig);


			echo "Ethernet connection : ";
			
			if(strpos($lines[1],"inet 192.168") != false)
			{
				?> <span class="ONstate">ON</span> <br /><br />  <?php
				//$ips = explode(" ", $lines[1]);
				$ips = preg_split('/\s+/', $lines[1]);
				echo "IP address :$ips[2]";
			}
			else
			{
				?> <span class="OFFstate">OFF</span> <br /><br />  <?php
			}
        	?>

        	<form method="post" action="process1.php" enctype="multipart/form-data">
 
        		<p>
			Wifi hot spot :<br />
			<?php
			//Display hotspot button according to configuration 
			if($hotspot == 1)
			{
			?>
				<label class="container"> ON
					<input type="radio" name="hotspot" value ="on" checked="checked">
					<span class="checkmark"></span>
				</label>
                		<label class="container"> OFF
                        		<input type="radio" name="hotspot" value ="off">
                        		<span class="checkmark"></span>
                		</label>
			<?php
			}
			elseif($hotspot == 0)
			{
			?>
                                <label class="container"> ON
                                        <input type="radio" name="hotspot" value ="on">
                                        <span class="checkmark"></span>
                                </label>
                                <label class="container"> OFF
                                        <input type="radio" name="hotspot" value ="off" checked="checked">
                                        <span class="checkmark"></span>
                                </label>

			<?php
			}
			?>
            		</p>

		<input type="submit" value="Process form"/>
        	<br />

		</form>     

		</div> <!-- End of menu1-->

                <!--MENU 2 : LORA/CHIRPSTACK CONFIGURATION ---------------------------------------------------------------------------------------------------->

		<div id="menu2">
			
			<form method="post" action="process2.php" enctype="multipart/form-data">
			
			<p>
                        Import device list :<br />
                                <label class="text_field">
                                	<input type="file" name="devlist" />
                                </label>
                        </p>


			<input type="submit" value="Process form"/>
                	<br />

                	</form>     


		</div> <!-- End of menu2-->


		<!--MENU 3 : LTEM CONFIGURATION ---------------------------------------------------------------------------------------------------->
		<div id="menu3">

			<?php
			//Copy the log file
                        shell_exec("cp /home/ogate/LTEM/ltem.log /var/www/html");
			
			//Files path to be checked
			$dataFile='/home/ogate/LTEM/ltem.dat';
			$confFile='/home/ogate/LTEM/ltem.conf';

			//Open the files to be checked( connection status and configuration)
			$dataContent = file_get_contents($dataFile);
			$confContent = file_get_contents($confFile);
			//parse the files
			$dataLines = explode("\n", $dataContent);
			$confLines = explode("\n", $confContent);

			//echo "$ltemLines[0]";
			echo "LTE-M connection : ";
                  
                        if(strpos($dataLines[0],"1") != false)
                        {
                                ?> <span class="ONstate">ON</span>  <?php
                        }

                        else if(strpos($dataLines[0],"0") != false)
                        {
                                ?> <span class="OFFstate">OFF</span>   <?php
                        }
			?>
                        <br /><br /> 
			<?php

			//echo "$ltemLines[1]";
			echo "MQTT broker connection : ";

                        if(strpos($dataLines[3],"1") != false)
                        {
                                ?> <span class="ONstate">ON</span>  <?php
                        }

                        else if(strpos($dataLines[3],"0") != false)
                        {
                                ?> <span class="OFFstate">OFF</span> <?php 
                        } 
			?>
			<br /><br />
			<?php

			$rssi = substr($dataLines[1],5);
			echo "LTE-M RSSI : "; ?> <span class="OFFstate"> <?php echo "$rssi db"; ?> </span> <br /><br /> <?php

			$snr = substr($dataLines[2],4);
			echo "LTE-M RSSNR : "; ?> <span class="OFFstate"> <?php echo "$snr db"; ?> </span> <br /><br />

			<a href="ltem.log">
  			Download logs
			</a>
 			<br /><br />

		
			<?php
			//See if SSL is activated in configuration file
	                if(strpos($confLines[8],"1") != false)
                        {
				$ssl = 1;
			}
			else $ssl = 0;
			?>

                <form method="post" action="process3.php" enctype="multipart/form-data">

                        <p>
                        MQTT secured connection (SSL) :<br />
                        <?php
			//Display SSL buttons according to configuration 
			if($ssl == 1)
                        {
                        ?>
                                <label class="container"> ON
                                        <input type="radio" name="ssl" value ="on" checked="checked">
                                        <span class="checkmark"></span>
                                </label>
                                <label class="container"> OFF
                                        <input type="radio" name="ssl" value ="off">
                                        <span class="checkmark"></span>
                                </label>
                        <?php
                        }
                        elseif($ssl == 0)
                        {
                        ?>
                                <label class="container"> ON
                                        <input type="radio" name="ssl" value ="on">
                                        <span class="checkmark"></span>
                                </label>
                                <label class="container"> OFF
                                        <input type="radio" name="ssl" value ="off" checked="checked">
                                        <span class="checkmark"></span>
                                </label>

                        <?php
                        }
                        ?>
                        </p>


                        <p>
                        SIM card APN :<br />
                                <label class="text_field">
                                        <input type="text" name="apn"size="30"/>
                                </label>
                        </p>


 			<p>
            		Server URL :<br />
				<label class="text_field">
            				<input type="text" name="mqtt_url"size="30"/>
                		</label>
	    		</p>

            		<p>
            		Port :<br />
				<label class="text_field">
            				<input type="text" name="mqtt_port"size="10"/>
        			</label>   
	 		</p>

	    		<p>
            		Username :<br />
				<label class="text_field">
            				<input type="text" name="mqtt_usn"size="50"/>
        			</label>   
	 		</p>

            		<p>
            		Password :<br />
				<label class="text_field">
            				<input type="text" name="mqtt_pwd"size="50"/>
        			</label>   
	 		</p>

            		<p>
            		Client ID :<br />
				<label class="text_field">
            				<input type="text" name="mqtt_clid"size="30"/>
        			</label>   
	 		</p>

            		<p>
            		MQTT topic header publish path (uplink) :<br />
				<label class="text_field">
            				<input type="text" name="mqtt_pubhead"size="30"/>
        			</label>   
	 		</p>

                        MQTT topic header subscribe path (downlink) :<br />
                                <label class="text_field">
                                        <input type="text" name="mqtt_subhead"size="30"/>
                                </label>   
                        </p>

                        <p>
                        Server root CA certificate (SSL) :<br />
                                <label class="text_field">
                                        <input type="file" name="mqtt_server_certificate" />
                                </label>   
                        </p>


            		<p>
            		Client certificate (SSL) :<br />
				<label class="text_field">
            				<input type="file" name="mqtt_client_certificate" />
        			</label>   
	 		</p>

            		<p>
            		Client key (SSL) :<br />
				<label class="text_field">
            				<input type="file" name="mqtt_client_key" /><br />
        			</label>  
	  		</p>

                        <p>
                        Delete previous certificates :<br />

                        <label class="container"> yes
                            <input type="radio" name="del" value ="yes">
                            <span class="checkmark"></span>
                        </label>

                        <label class="container"> no
                            <input type="radio" name="del" value ="no" checked="checked">
                            <span class="checkmark"></span>
                        </label>
                        </p>
                        
                        <input type="submit" value="Process form"/>
                        <br />

                        </form>   

		</div><!-- End of menu3-->


	</div><!-- End of body-->

        <div class="footer">
            <p>Need help? Visit <a href="https://www.atim.com/en/technical-support/"> www.atim.com/en/technical-support</a></p>
        </div>

    </body>
</html>
