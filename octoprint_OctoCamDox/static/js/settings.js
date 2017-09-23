$(function() {
    function OctoCamDoxSettingsViewModel(parameters) {
        var self = this;
        self.settings = parameters[0];

        self.target_folder = ko.observable();
        self.picture_width = ko.observable();
        self.picture_height = ko.observable();

        self.UpdateLabels = function(input) {
            self.target_folder(input[0]);
            self.picture_width(input[1]);
            self.picture_height(input[2]);
        };

        self.getImageRes = function() {
            console.log("Updating Camera Resolution, make sure the printer is online!");
            $.ajax({
                url: "api" + PLUGIN_BASEURL + "OctoCamDox",
                type: "GET",
                dataType: "json",
                contentType: "application/json; charset=UTF-8",
                //data: JSON.stringify(data),
                success: function(response) {
                    if(response.hasOwnProperty("width")) {
                        self.picture_width(response.width);
                    }
                    if(response.hasOwnProperty("height")) {
                        self.picture_height(response.height);
                    }
                    if(response.hasOwnProperty("error")) {
                        alert(response.error);
                    }
                }
            });
        };

        // This will get called before the HelloWorldViewModel gets bound to the DOM, but after its
        // dependencies have already been initialized. It is especially guaranteed that this method
        // gets called _after_ the settings have been retrieved from the OctoPrint backend and thus
        // the SettingsViewModel been properly populated.
        self.onBeforeBinding = function() {
            self.UpdateLabels(
              [self.settings.settings.plugins.OctoCamDox.target_folder(),
              self.settings.settings.plugins.OctoCamDox.picture_width(),
              self.settings.settings.plugins.OctoCamDox.picture_height()]);
        };
    }
    // This is how our plugin registers itself with the application, by adding some configuration information to
    // the global variable ADDITIONAL_VIEWMODELS
    OCTOPRINT_VIEWMODELS.push({
        // This is the constructor to call for instantiating the plugin
        construct: OctoCamDoxSettingsViewModel,

        // This is a list of dependencies to inject into the plugin, the order which you request here is the order
        // in which the dependencies will be injected into your view model upon instantiation via the parameters
        // argument
        // dependencies: ["settingsViewModel", "controlViewModel", "connectionViewModel"],
        dependencies: ["settingsViewModel"],

        // Finally, this is the list of all elements we want this view model to be bound to.
        elements:["#settings_plugin_OctoCamDox"]
    });
});
