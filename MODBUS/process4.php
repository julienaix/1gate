
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

	#!/bin/su root
        $tableFile='/home/ogate/MODBUS/modbus.dev';
        echo "<br \>";

        //Clear device list

	$fp = fopen($tableFile, 'w');
	fclose($fp);
        
        echo "Device table has been cleared";
        echo "<br \>";
        echo "MODBUS service is restarting";
        echo "<br \>";
	//Restart modbus program
	shell_exec('sudo systemctl restart modbus');
        ?>

        </div>        

        <div class="footer">
            <p>Need help? Visit <a href="https://www.atim.com/en/technical-support/"> www.atim.com/en/technical-support</a></p>
        </div>

    </body>
</html>
