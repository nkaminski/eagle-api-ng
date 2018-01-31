from lxml import etree
from lxml import objectify
from . import exceptions

class Device():
    #Initializes a device class object with the initial set of attributes returned by the device_list call, passed as a dict
    def __init__(self, api, data):
        self.components = None
        self.api = api
        for key, val in data.items():
            setattr(self, key, val)
    
    #Makes a device_details API call to populate the components dictionary with all avaliable variables
    def query_device_details(self, refresh=False):
        #If device has been queried, return the current value of the components dict unless we specifically want to refresh
        if(self.components and (not refresh)):
            return self.components

        self.components = dict()
        #Build the query
        x_root = self.api.construct_root('device_details', self.HardwareAddress)
       
        #Send it and parse the result
        response = self.api.send_request(etree.tostring(x_root, pretty_print=self.api.debug))
        responseobj = objectify.fromstring(response.text)
        
        #error checks
        err = self.api.check_error(responseobj)
        if(err):
            raise exceptions.EAGLEError(err)

        self.components = self.parse_components(responseobj.Components)
        return self.components

    #Makes a device_query API call to query the value of a set of variables, passed as a dictionary of form {"component_name": ["variable_names"]}
    def query_device_values(self, qdict, strip_units=False):
        x_root = self.api.construct_root('device_query', self.HardwareAddress)
        x_root.append(self.build_components(qdict))
        
        #Send it and parse the result
        response = self.api.send_request(etree.tostring(x_root, pretty_print=self.api.debug))
        responseobj = objectify.fromstring(response.text)

        #error checks
        err = self.api.check_error(responseobj)
        if(err):
            raise exceptions.EAGLEError(err)

        return self.parse_components(responseobj.Components,True,strip_units)

    #Builds a Component etree hierarchy, using a dict of the form {"component_name": [variable_names]} or {"component_name": {variable_name: variable_value}}
    def build_components(self, qdict):
        #Build the tree, making sure all variables are supported
        #First, build all required structures
        supported = self.query_device_details()
        x_components = etree.Element('Components')
        
        #For each component
        for k, v in qdict.items():
            #Build structures
            x_component = etree.Element('Component')
            x_compname = etree.Element('Name')
            x_variables = etree.Element('Variables')

            #Check the component name to make sure it is supported, then prepare to add to etree
            if not (k in self.components.keys()):
                raise ValueError("Unsupported component name")

            #Prepare the Component element attributes
            x_compname.text=k
            x_component.append(x_compname)
            
            #For each variable, make sure it is supported, then prepare to add to etree.
            if(isinstance(v, dict)):
                for var in v.items():
                    #Add a variable->value pair to the list of variables
                    if not (var[0] in self.components[k]):
                        raise AttributeError("Unsupported variable name")
                    x_var = etree.Element('Variable')
                    x_varname = etree.Element('Name')
                    x_varvalue = etree.Element('Value')
                    x_varname.text = var[0]
                    x_varvalue.text = str(var[1])
                    x_var.append(x_varname)
                    x_var.append(x_varvalue)
                    x_variables.append(x_var)

            else:
                for var in v:
                    #Add a variable only
                    if not (var in self.components[k]):
                        raise AttributeError("Unsupported variable name")
                    x_var = etree.Element('Variable')
                    x_varname = etree.Element('Name')
                    x_varname.text = var
                    x_var.append(x_varname)
                    x_variables.append(x_var)

                
            # Add the variables node to the component
            x_component.append(x_variables)
            # Add the new component node as a child of the components node
            x_components.append(x_component)

        return x_components
    

    #Parses a Component etree hierarchy represented as an object into a dict of the form {"component_name": [variable_names]} or {"component_name": {variable_name: variable_value}}
    def parse_components(self, comp_obj, with_values=False, strip_units=False):
        components = dict()
        #For each component, access all variables
        for component in comp_obj.iterchildren():
            #Nested object is a list if we are just returning names, otherwise it is a dict
            if(with_values):
                var_list = dict()
            else:
                var_list = list()
            for variable in component.Variables.iterchildren():
                #Are we parsing a response with values in it?
                if(with_values):
                    var = variable.Value.text
                    if(var and strip_units):
                        #Strip units from the values if specified
                        var_list[variable.Name.text] = variable.Value.text.partition(' ')[0]
                    else:
                        # Just add the key/value pair
                        var_list[variable.Name.text] = variable.Value.text
                else:
                    #No values requested, so we are building a list of names
                    var_list.append(variable.text)
            components[component.Name.text] = var_list
        return components
    
    def __str__(self):
        return str(self.__dict__)


