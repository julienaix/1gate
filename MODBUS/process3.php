<html xmlns = "http://www.w3.org/1999/xhtml" xml:lang="fr" lang="fr">

    <head>
        <title>1gate configurator</title>
        <meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1"/>
        <link href="style.css?v=4" rel="stylesheet" type="text/css"/>
    </head>

    <body>

        <div class="header">

            <p><a href="index.php"><img src="img/atim.png" alt="ATIM"></a></p>

            <h1>
            Gateway API configurator
            </h1>

        </div>

        <div class="body">

        <?php
        $file_path='/home/ogate/LTEM/ltem.conf';
        echo "<br \>";
 
        //0.Check the state of SSH buttons

	if($_POST['ssh'] == "on")
        {
                echo "MQTT connection is secured (SSH)";
                echo "<br \>";
		//Open configuration file and update ssh configuration
		$file_content=file_get_contents($file_path);
                //Find the ssh line on the file and replace by new value
                $new_content = preg_replace("#mqttSSH=(.*)\n#","mqttSSH=1\n",$file_content);
                //Replace with new content
                file_put_contents($file_path, $new_content);

        }
        elseif($_POST['ssh'] == "off")
        {
                echo "MQTT connection is not secured";
                echo "<br \>";
                //Open configuration file and update ssh configuration
                $file_content=file_get_contents($file_path);
                //Find the ssh line on the file and replace by new value
                $new_content = preg_replace("#mqttSSH=(.*)\n#","mqttSSH=0\n",$file_content);
                //Replace with new content
                file_put_contents($file_path, $new_content);
        }


        //1.Check the APN address
        if($_POST['apn'] != NULL)
        {
                $apn = $_POST['apn'];
                echo "Changed the SIM card APN address to : $apn";
                echo "<br \>";
                //Open the configuration file
                $file_content=file_get_contents($file_path);
                //Find the apn address line on the file and replace by new address
                $new_content = preg_replace("#ltemAPN=(.*)\n#","ltemAPN=$apn\n",$file_content);
                //Replace with new content
                file_put_contents($file_path, $new_content);
        }

	//2.Check the MQTT server URL
        if($_POST['mqtt_url'] != NULL)
        {
                $url = $_POST['mqtt_url'];
                echo "Changed the MQTT server URL to : $url";
                echo "<br \>";
                //Open the configuration file
                $file_content=file_get_contents($file_path);
                //Find the line on the file and replace by new one
                $new_content = preg_replace("#mqttURL=(.*)\n#","mqttURL=$url\n",$file_content);
                //Replace with new content
                file_put_contents($file_path, $new_content);
        }

	//3.Check the MQTT server port
        if($_POST['mqtt_port'] != NULL)
        {
                $prt = $_POST['mqtt_port'];
                echo "Changed the MQTT server port to : $prt";
                echo "<br \>";
                //Open the configuration file
                $file_content=file_get_contents($file_path);
                //Find the line on the file and replace by new one
                $new_content = preg_replace("#mqttPort=(.*)\n#","mqttPort=$prt\n",$file_content);
                //Replace with new content
                file_put_contents($file_path, $new_content);
        }

	//4.Check the MQTT server username
        if($_POST['mqtt_usn'] != NULL)
        {
                $usn = $_POST['mqtt_usn'];
                echo "Changed the MQTT username to : $usn";
                echo "<br \>";
                //Open the configuration file
                $file_content=file_get_contents($file_path);
                //Find the line on the file and replace by new one
                $new_content = preg_replace("#mqttUsername=(.*)\n#","mqttUsername=$usn\n",$file_content);
                //Replace with new content
                file_put_contents($file_path, $new_content);
        }

	//5.Check the MQTT server password
        if($_POST['mqtt_pwd'] != NULL)
        {
                $pwd = $_POST['mqtt_pwd'];
                echo "Changed the MQTT password to : $pwd";
                echo "<br \>";
                //Open the configuration file
                $file_content=file_get_contents($file_path);
                //Find the line on the file and replace by new one
                $new_content = preg_replace("#mqttPassword=(.*)\n#","mqttPassword=$pwd\n",$file_content);
                //Replace with new content
                file_put_contents($file_path, $new_content);
        }

	//6.Check the MQTT server topic header
        if($_POST['mqtt_head'] != NULL)
        {
                $head = $_POST['mqtt_head'];
                echo "Changed the MQTT server topic header to : $head";
                echo "<br \>";
                //Open the configuration file
                $file_content=file_get_contents($file_path);
                //Find the line on the file and replace by new one
                $new_content = preg_replace("#mqttHeader=(.*)\n#","mqttHeader=$head\n",$file_content);
                //Replace with new content
                file_put_contents($file_path, $new_content);
        }

	//7.Check the MQTT Cliend Id
        if($_POST['mqtt_clid'] != NULL)
        {
                $clid = $_POST['mqtt_clid'];
                echo "Changed the MQTT client ID to : $clid";
                echo "<br \>";
                //Open the configuration file
                $file_content=file_get_contents($file_path);
                //Find the line on the file and replace by new one
                $new_content = preg_replace("#mqttClid=(.*)\n#","mqttClid=$clid\n",$file_content);
                //Replace with new content
                file_put_contents($file_path, $new_content);
        }

        //8.Upload the MQTT broker server root CA certificate

        //test if file has been uploaded without errors
        if(isset($_FILES['mqtt_server_certificate']) AND $_FILES['mqtt_server_certificate']['error'] == 0)
        {

                //Check the type of the file (must be .cer)
                $file_data = pathinfo($_FILES['mqtt_server_certificate']['name']); 
                $file_type = $file_data['extension'];
		//!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!TO BE COMPLETED
                $extension = array('cer');

                if(in_array($file_type, $extension))
                {
                        //Move the temporary file uploaded to API folder
                        move_uploaded_file($_FILES['mqtt_server_certificate']['tmp_name'], '/home/ogate/LTEM/certificates/server.cer');
                        echo "Server CA certificate has been uploaded and saved";
                        echo "<br \>";
                }   
                else
                {
                        echo "Error uploading server CA certificate : wrong extension";
                        echo "<br \>";
                }

        }
        elseif($_FILES['mqtt_client_certificate']['error'] == 1)
        {
                echo "Error uploading server CA certificate";
                echo "<br \>";
        }


	//9.Upload the client (self signed) certificate

        //test if file has been uploaded without errors
        if(isset($_FILES['mqtt_client_certificate']) AND $_FILES['mqtt_client_certificate']['error'] == 0)
        {

                //Check the type of the file (must be .cer)
                $file_data = pathinfo($_FILES['mqtt_client_certificate']['name']); 
                $file_type = $file_data['extension'];
                $extension = array('cer');

                if(in_array($file_type, $extension))
                {
                        //Move the temporary file uploaded to API folder
                        move_uploaded_file($_FILES['mqtt_client_certificate']['tmp_name'], '/home/ogate/LTEM/certificates/module.cer');
                        echo "Client certificate has been uploaded and saved";
                        echo "<br \>";
                }   
                else
                {
                        echo "Error uploading client certificate : wrong extension";
                        echo "<br \>";
                }

        }
        elseif($_FILES['mqtt_client_certificate']['error'] == 1)
        {
                echo "Error uploading client certificate";
                echo "<br \>";
        }


	//10.Upload the client key

	//test if file has been uploaded without errors
        if(isset($_FILES['mqtt_client_key']) AND $_FILES['mqtt_client_key']['error'] == 0)
        {

                //Check the type of the file (must be .key)
                $file_data = pathinfo($_FILES['mqtt_client_key']['name']); 
                $file_type = $file_data['extension'];
                $extension = array('key');

                if(in_array($file_type, $extension))
                {
                        //Move the temporary file uploaded to API folder
                        move_uploaded_file($_FILES['mqtt_client_key']['tmp_name'], '/home/ogate/LTEM/certificates/module.key');
                        echo "Client key has been uploaded and saved";
                        echo "<br \>";
                }   
                else
                {
                        echo "Error uploading client key : wrong extension";
                        echo "<br \>";
                }

        }
        elseif($_FILES['mqtt_client_key']['error'] == 1)
        {
                echo "Error uploading client key";
                echo "<br \>";
        }

	?>

        </div><!--End of class body-->        

        <div class="footer">
            <p>Need help? Visit <a href="https://www.atim.com/en/technical-support/"> www.atim.com/en/technical-support</a></p>
        </div>

    </body>
</html>

