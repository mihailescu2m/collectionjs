collectionjs
============

CollectionJS - export RRD data from collectd daemon to Highcharts

### Installation

To install and run CollectionJS, just copy the files in your web server folder, make sure cgi scripts can run, and open up a browser window.

Example apache configuration:
```
    Alias /collectionJS /var/www/collectionJS
    <Directory /var/www/collectionJS/>
            AddHandler cgi-script .cgi
            DirectoryIndex index.html
            Options +ExecCGI
            Order Allow,Deny
            Allow from all
    </Directory>
```

### Structure

* bin

   Contains several perl scripts required by CollectionJS:
     * **getHosts.cgi** - returns a JSON object containing available hosts and plugins. In the example index.html, the script is used to populate the dropdown menus.
     * **getPlugins.cgi** - expects as parameters a hostname and a plugin, and it returns a JSON array with available charts, containing information such as *plugin_instance*, *type*, and *type_instance*
     * **getChart.cgi** - based on collection3's *graph.cgi*, it returns the data required for highcharts in JSON format.

* etc

   Contains the graph definitions from collection3

* lib

    Contains collection3's perl scripts to create a chart definition, which is then sent by *getChart* in JSON format
    It also contains **collection.js**, a set of javascript functions to create the highcharts data structures, theme, and render the graphs.

* index.html

    Example html code using twitter bootstrap.


