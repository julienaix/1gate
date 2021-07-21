<html xmlns = "http://www.w3.org/1999/xhtml" xml:lang="fr" lang="fr">

    <head>
        <title>ATIM gateway API</title>
        <meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1"/>
        <link href="style.css" rel="stylesheet" type="text/css"/>
    </head>

    <body>

        <div class="header">

            <p><a href="index.php"><img src="img/atim.png" alt="ATIM"></a></p>

            <h1>
            1gate configurator
            </h1>

        </div>

        <div class="body">

        <?php
	        
        echo "<br \>";

        //1.Check the state of ethernet

	//Open configuration file
        $dhcpFile='/etc/dhcpcd.conf';
	//Get content of the file
        $dhcpContent = file_get_contents($dhcpFile);
        //Parse the lines
        $dhcpLines = explode("\n", $dhcpContent);
	//Count the lines
        $dhcpCnt = count($dhcpLines);


        if($_POST['ethernet'] == "dhcp")
        {
                echo "Ethernet is configured using DHCP";
                echo "<br \>";

                //Delete the last configuration lines
                $fp = fopen($dhcpFile, 'w');
                for($i = 0; $i < 40; $i++ )
                {
                        fwrite($fp,$dhcpLines[$i]);
                        fwrite($fp,"\n");
                }
		fclose($fp);

                shell_exec('sudo ifconfig eth0 up');                
        }

        else if($_POST['ethernet'] == "static")
        {
		//Check if IP adress field has been filled
		if( isset($_POST['ethIP']) && strlen($_POST['ethIP']) ) 
		{
                        echo "Ethernet is configured using static IP : ";
                        echo $_POST['ethIP'];
                        echo "<br \>";
		}
		else 
		{
                        echo "ERROR : Ethernet IP static address is missing";
                        echo "<br \>";
		}

		//Delete the last configuration lines
		$fp = fopen($dhcpFile, 'w');
		for($i = 0; $i < 40; $i++ )
                {
			fwrite($fp,$dhcpLines[$i]);
			fwrite($fp,"\n");
		}
		//Add the lines for static IP configuration
		fwrite($fp,"interface eth0\n");
		fwrite($fp,"static ip_address=");
                fwrite($fp, $_POST['ethIP']);
		fwrite($fp, "/");
		fwrite($fp, $_POST['ethMASK']);
                fwrite($fp, "\nstatic routers=");
                fwrite($fp, $_POST['ethGW']);
		fclose($fp);

                //Turn peripheral ON
                shell_exec('sudo ifconfig eth0 up');
        }



	/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        //2.Check the state of wifi

        if($_POST['ethernet'] == "static" && $_POST['wifi'] == "static")
        {
                echo "ERROR : WIFI and Ethernet are configured with static address - Priority is given to WIFI";
                echo "<br \>";
        }


        if($_POST['wifi'] == "dhcp")
        {
                echo "WIFI is configured using DHCP";
                echo "<br \>";
                
		if($_POST['ethernet'] != "static")
		{
                	//Delete the last configuration lines
                	$fp = fopen($dhcpFile, 'w');
                	for($i = 0; $i < 40; $i++ )
                	{
                        	fwrite($fp,$dhcpLines[$i]);
                        	fwrite($fp,"\n");
                	}
			fclose($fp);
                }
		shell_exec('sudo rfkill unblock wifi');
		
        }

        elseif($_POST['wifi'] == "static" && $_POST['ethernet'] != "static" )
        {
                //Check if IP address has been filled
                if ( isset($_POST['wlanIP']) && strlen($_POST['wlanIP']) ) 
                {
                        echo "WIFI is configured using static IP : ";
                        echo $_POST['wlanIP'];
                        echo "<br \>";
                }
                else 
                {
                        echo "ERROR : WIFI IP static address is missing ";
                        echo "<br \>";
                }

                //Delete the last configuration lines
                $fp = fopen($dhcpFile, 'w');
                for($i = 0; $i < 40; $i++ )
                {
                        fwrite($fp,$dhcpLines[$i]);
                        fwrite($fp,"\n");
                }
                //Add the lines for static IP configuration
                fwrite($fp,"interface wlan0\n");
                fwrite($fp,"static ip_address=");
                fwrite($fp, $_POST['wlanIP']);
		fwrite($fp, "/");
                fwrite($fp, $_POST['wlanMASK']);
                fwrite($fp, "\nstatic routers=");
                fwrite($fp, $_POST['wlanGW']);
                fclose($fp);

     	        //Turn peripheral ON
                shell_exec('sudo ifconfig wlan0 up');

	}

        elseif($_POST['wifi'] == "off")
        {
                echo "Wifi peripheral is turned OFF";
                echo "<br \>";
                shell_exec('sudo rfkill block wifi');
        }
        ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        //3.Check if a wifi network has been registered

	if( isset($_POST['ssid']) && strlen($_POST['ssid']) )
	{
		//Open wifi network file
        	$wifiFile='/etc/wpa_supplicant/wpa_supplicant.conf';
        	//Get content of the file
        	$wifiContent = file_get_contents($wifiFile);
        	//Parse the lines
        	$wifiLines = explode("\n", $wifiContent);
        	//Count the lines
        	$wifiCnt = count($wifiLines);
		echo "WIFI network ";
                echo($_POST['ssid']);
		echo " is registered";
                echo "<br \>";
		
		$fp = fopen($wifiFile, 'w');
                for($i = 0; $i < $wifiCnt; $i++ )
                {
                        fwrite($fp,$wifiLines[$i]);
			//echo($wifiLines[$i]);
                        fwrite($fp,"\n");
                }

		//Add the new lines
		fwrite($fp, "network={\n    ssid=\"");
		fwrite($fp, $_POST['ssid']);
		fwrite($fp, "\"\n    psk=\"");
		fwrite($fp, $_POST['password']);
		fwrite($fp, "\"\n}");
		fclose($fp);
		
	}


	//Reboot the gateway
        shell_exec('sudo systemctl restart networking');
	echo "Gateway needs to be restarted ...";
        
	
	?>
	
	<form method="post" action="restart.php" enctype="multipart/form-data">

	<input type="submit" value="RESTART"/>

	</form>

	</div>

        <div class="footer">
            <p>Need help? Visit <a href="https://www.atim.com/en/technical-support/"> www.atim.com/en/technical-support</a></p>
        </div>

    </body>
</html>


