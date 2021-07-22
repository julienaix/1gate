<html xmlns = "http://www.w3.org/1999/xhtml" xml:lang="fr" lang="fr">

    <head>
        <title>ATIM gateway API</title>
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
	
	echo "<br \>";
	//1.Upload device list

	//test if file has been uploaded without errors
	if(isset($_FILES['devlist']) AND $_FILES['devlist']['error'] == 0)
	{

		//Check the type of the file (must be .cer)
		$file_data = pathinfo($_FILES['devlist']['name']); 
		$file_type = $file_data['extension'];
                $extension = array('csv','txt');
		
		if(in_array($file_type, $extension))
		{
			//Move the temporary file uploaded to API folder
			move_uploaded_file($_FILES['devlist']['tmp_name'], '/home/ogate/API/devlist.csv');
                        echo "Device list has been uploaded and saved";
                        echo "<br \>";

			//Run the script to add the devices on Chirpstack				
			shell_exec('bash /home/ogate/API/add_devices.sh');
		}   
		else
		{
                	echo "Error uploading device list : wrong extension";
                	echo "<br \>";
		}

	}
	elseif($_FILES['server_certificate']['error'] == 1)
	{
		echo "Error uploading device list";
		echo "<br \>";
	}

	?>

	</div>        

        <div class="footer">
            <p>Need help? Visit <a href="https://www.atim.com/en/technical-support/"> www.atim.com/en/technical-support</a></p>
        </div>

    </body>
</html>
