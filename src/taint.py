"""
    taint analyse and contract slice
    Input:
        Hc
    
    Output:
        taint propagation graph
        code snippet
"""

from slither.core.declarations import (
    Function,
    Contract,
    SolidityVariableComposed,
)
from slither.core.expressions import CallExpression
from slither.core.expressions.expression import Expression
from slither.core.compilation_unit import SlitherCompilationUnit

GENERIC_TAINT = {
    SolidityVariableComposed("msg.sender"),
    SolidityVariableComposed("msg.value"),
    # SolidityVariableComposed("msg.data"),
    # SolidityVariableComposed("tx.origin"),
    # SolidityVariableComposed("tx.gasprice"),
}

###################################################################################
# region taint API
###################################################################################

class TaintPropagation:
    def __init__(self, compilation_unit: SlitherCompilationUnit, granularity: str) -> None:
        self.compilation_unit = compilation_unit
        self.granularity = granularity
        
        self.global_taints = {
            'msg.sender',
            'msg.value',
            # 'msg.data',
            # 'tx.origin',
            # 'tx.gasprice',
        }
        
        self.local_taints = {}
        self.other_taints = set()
        self.taint_nodes: dict[str: TaintPropagationNode] = {}
        
        self.taint_nodes['msg.sender'] = TaintPropagationNode(
            'msg.sender',
            None, 
            SolidityVariableComposed("msg.sender"),
            'SolidityVariable'
        )

        self.taint_nodes['msg.value'] = TaintPropagationNode(
            'msg.value',
            None, 
            SolidityVariableComposed("msg.value"),
            'SolidityVariable'
        )

        self.taint_functions: list[Function] = []
        self.tanit_returns: list[Function] = []
        self.taint_functions_name: list[str] = []
        self.taint_contracts: list[Contract] = []
        self.taint_contracts_name: list[str] = []
        self.analysed_functions: list[str] = []
        self.dot, self.snippet = self.taint_propagation()

    def taint_return(self, f: Function):
        flag = True
        return_values = [v for v in f.return_values]
        var_taints = self.global_taints.union(self.local_taints[f.full_name])
        
        for v in return_values:
            if hasattr(v, 'name'):
                if v.name in var_taints:
                    if flag:
                        node = TaintPropagationNode(
                            name=f.full_name,
                            expression=None,
                            variable=f,
                            domain='FunctionContract'
                        )
                        
                        self.other_taints.add(f.full_name)
                        self.taint_nodes[f.full_name] = node
                        flag = False
                    
                    if not f.full_name in self.taint_nodes[v.name].name_list:
                        self.taint_nodes[v.name].name_list.append(f.full_name)
                        self.taint_nodes[v.name].propagation_list.append(
                            {
                                f.full_name: node
                            }
                        )

    def taint_source_function(self):
        """
            taint source function list
        """

        source_functions = []
        source_names = []
        
        for c in self.compilation_unit.contracts:
            for f in c.functions:
                if GENERIC_TAINT & set(f.solidity_variables_read):
                    if f.full_name not in source_names:
                        source_names.append(f.full_name)
                        source_functions.append(f)

        return source_functions

    def taint_sink_function(self):
        """
            taint sink function list
        """

        sink_functions = []
        sink_names = []
        for c in self.compilation_unit.contracts:
            for f in c.functions:
                if not {'value', 'transfer'}.isdisjoint(set(e.called.member_name for e in f.calls_as_expressions if hasattr(e.called, 'member_name'))):
                    if f.full_name not in sink_names:
                        sink_names.append(f.full_name)
                        sink_functions.append(f)

        return sink_functions

    def find_variable_of_lvalue(self, lv: Expression):
        if hasattr(lv, 'value'):
            return lv.value
        
        elif hasattr(lv, 'expression_left'):
            return self.find_variable_of_lvalue(lv.expression_left)
        
        elif hasattr(lv, 'expression'):
            return self.find_variable_of_lvalue(lv.expression)

    def expression_parse(self, e: Expression, f: Function):
        """
            expression parse: left value and taints in expression
        """
        
        expression_lvalue = None
        expression_taints = []

        # call process
        if isinstance(e, CallExpression):
            if e.type_call != 'Modifier':
                if hasattr(e.called, 'value') and isinstance(e.called.value, Function):
                    if not e.called.value.full_name in self.taint_functions_name:
                        arg_index = {} # index of taint args
                        for arg in e.arguments:
                            lv, taints = self.expression_parse(arg, f) # parse arg expression
                            if taints != []:
                                arg_index[e.arguments.index(arg)] = taints
                                for t in taints:
                                    expression_taints.append(t)

                        if arg_index != {}:
                            if not e.called.value.full_name in self.taint_functions_name:
                                self.taint_functions_name.append(e.called.value.full_name)
                                self.taint_functions.append(e.called.value)

                            self.function_node_analyse(e.called.value, arg_index)

                    if e.called.value.full_name in self.other_taints:
                        expression_taints.append(e.called.value.full_name)

        else:
            if hasattr(e, 'expression_left'):
                lvalue_left, taints_left = self.expression_parse(e.expression_left, f)
                if taints_left != []:
                    for t in taints_left:
                        expression_taints.append(t)
                
                if lvalue_left != None:
                    expression_lvalue = lvalue_left

            if hasattr(e, 'expression_right'):
                lvalue_right, taints_right = self.expression_parse(e.expression_right, f)
                if taints_right != []:
                    for t in taints_right:
                        expression_taints.append(t)
                
                if lvalue_right != None:
                    expression_lvalue = lvalue_right

            if e.is_lvalue:
                expression_lvalue = e

            if hasattr(e, 'value'):
                if hasattr(e.value, 'name'):
                    if e.value.name in self.global_taints or e.value.name in self.local_taints[f.full_name]:
                        expression_taints.append(e.value.name)

            elif e.source_mapping != None:
                if e.source_mapping.content in self.global_taints or e.source_mapping.content in self.local_taints[f.full_name]:
                    expression_taints.append(e.source_mapping.content)

        return expression_lvalue, expression_taints

    def expression_analyse(self, e: Expression, f: Function) -> None:
        """
            expression analyse
        """

        expression_lvalue, expression_taints = self.expression_parse(e, f)
        if expression_lvalue != None:
            if expression_lvalue.source_mapping != None:
                name = expression_lvalue.source_mapping.content
            else:
                name = expression_lvalue.value.name
            
            if name not in self.global_taints and name not in self.local_taints[f.full_name]:
                if expression_taints != []:
                    if not f.full_name in self.taint_functions_name:
                        self.taint_functions_name.append(f.full_name)
                        self.taint_functions.append(f)

                    lv_var = self.find_variable_of_lvalue(expression_lvalue)
                    if lv_var.__class__.__name__ == 'StateVariable':
                        node = TaintPropagationNode(
                            name,
                            expression_lvalue,
                            lv_var,
                            f.contract
                        )
                        
                        self.global_taints.add(name)
                        self.taint_nodes[name] = node

                    elif lv_var.__class__.__name__ == 'LocalVariable':
                        node = TaintPropagationNode(
                            name,
                            expression_lvalue,
                            lv_var,
                            f
                        )
                        
                        if not hasattr(self.local_taints, f.full_name):
                            self.local_taints[f.full_name] = set()
                        
                        self.local_taints[f.full_name].add(name)
                        self.taint_nodes[name] = node

                    else:
                        node = TaintPropagationNode(
                            name,
                            expression_lvalue,
                            lv_var,
                            None
                        )
                        
                        self.other_taints.add(name)
                        self.taint_nodes[name] = node

                    for taint in expression_taints:
                        if taint != name:
                            if not name in self.taint_nodes[taint].name_list:
                                self.taint_nodes[taint].name_list.append(name)
                                self.taint_nodes[taint].propagation_list.append(
                                    {
                                        name: node
                                    }
                                )

    def function_node_analyse(self, f: Function, args_tainted: dict) -> None:
        """
            function node analyse: CFG node taint analyse
        """
        
        if f.full_name not in self.taint_functions_name or f.full_name not in self.analysed_functions:
            if not hasattr(self.local_taints, f.full_name):
                self.local_taints[f.full_name] = set()

            if args_tainted != {}:
                for k in args_tainted.keys():
                    name = f.parameters[k].name
                    self.local_taints[f.full_name].add(name)

                    self.taint_nodes[name] = TaintPropagationNode(
                        name,
                        None,
                        f.parameters[k],
                        f
                    )

                    for t in args_tainted[k]:
                        if t != name:
                            if not name in self.taint_nodes[t].name_list:
                                self.taint_nodes[t].name_list.append(name)
                                self.taint_nodes[t].propagation_list.append(
                                    {
                                        name: self.taint_nodes[name]
                                    }
                                )

            for n in f.nodes:
                if n.expression != None:
                    self.expression_analyse(n.expression, f)

            self.taint_return(f)

            if f.full_name not in self.analysed_functions:
                self.analysed_functions.append(f.full_name)

        else:
            pass

    def taint_propagation(self) -> None:
        """
            taint propagation
        """

        source_functions = self.taint_source_function()
        sink_functions = self.taint_sink_function()

        for function in source_functions:
            self.taint_functions.append(function)
            self.taint_functions_name.append(function.full_name)
            self.function_node_analyse(function, {})

        while(True):
            before = len(self.taint_functions_name)

            for contract in self.compilation_unit.contracts:
                for function in contract.functions:
                    self.function_node_analyse(function, {})

            after = len(self.taint_functions_name)

            if before == after:
                break

        for f in self.taint_functions:
            if not f.contract.name in self.taint_contracts_name:
                self.taint_contracts_name.append(f.contract.name)
                self.taint_contracts.append(f.contract)

        graph = TaintPropagationGraph(self.taint_nodes, self.taint_functions, self.taint_contracts)
        graph.add_edge()

        for function in sink_functions:
            if not function.full_name in self.taint_functions_name:
                graph.functions.append(function)
            if not function.contract.name in self.taint_contracts_name:
                graph.contracts.append(function.contract)

        if self.granularity == 'contract':
            return graph.export_dot(), graph.contract_snippet()
        
        else:
            return graph.export_dot(), graph.function_snippet()

class TaintPropagationNode:
    def __init__(self, name, expression, variable, domain) -> None:
        self.name = name
        self.expression = expression
        self.variable = variable
        self.domain = domain
        self.propagation_list = []
        self.name_list = []

class TaintPropagationGraph:
    def __init__(self, nodes: list[TaintPropagationNode], functions: list[Function], contracts: list[Contract]): 
        self.nodes = nodes
        self.functions = functions
        self.contracts = contracts
        self.edges = []
        
    def add_edge(self):
        for node in self.nodes.values():
            source = node.name
            for d in node.propagation_list:
                for n in d.values():
                    target = n.name
                
                self.edges.append((self.nodes[source], self.nodes[target]))

    def export_dot(self):
        dot = "digraph {\n"
        
        for node in self.nodes.values():
            dot += f'\t{node.name};\n'

        for edge in self.edges: 
            src = edge[0].name
            dst = edge[1].name
            dot += f'\t{src} -> {dst};\n'
        
        dot += "}"
        return dot
    
    def function_snippet(self):
        snippet = '```solidity\n'
        for f in self.functions:
            snippet = snippet + f.source_mapping.content + '\n'

        snippet += '```'

        return snippet
    
    def contract_snippet(self):
        snippet = '```solidity\n'
        for c in self.contracts:
            snippet = snippet + c.source_mapping.content + '\n'

        snippet += '```'
        
        return snippet
