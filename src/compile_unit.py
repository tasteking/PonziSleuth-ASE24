"""
    compilation_unit: compile solidity file, parse ast to compile unit
"""

import regex
from taint import TaintPropagation
from slither.exceptions import SlitherException, SlitherError
from crytic_compile import CryticCompile, InvalidCompilation
from slither.core.compilation_unit import SlitherCompilationUnit
from slither.vyper_parsing.ast.ast import parse
from slither.vyper_parsing.vyper_compilation_unit import VyperCompilationUnit
from slither.solc_parsing.slither_compilation_unit_solc import SlitherCompilationUnitSolc
from typing import Union, List
from slither.core.slither_core import SlitherCore

def _update_file_scopes(sol_parser: SlitherCompilationUnitSolc):
    """
    Since all definitions in a file are exported by default, including definitions from its (transitive) dependencies,
    we can identify all top level items that could possibly be referenced within the file from its exportedSymbols.
    It is not as straightforward for user defined types and functions as well as aliasing. See add_accessible_scopes for more details.
    """
    candidates = sol_parser.compilation_unit.scopes.values()
    learned_something = False
    # Because solc's import allows cycle in the import graph, iterate until we aren't adding new information to the scope.
    while True:
        for candidate in candidates:
            learned_something |= candidate.add_accessible_scopes()
        if not learned_something:
            break
        learned_something = False

def get_solc_version(code):
    """
        get solidity version from code
    """
    min_version = '0.4.11'
    try:
        versions = regex.finditer(r'pragma\ssolidity\s*\D*(\d+\.\d+\.\d+)', code)
    except:
        print('use minimum version that works')
        return min_version

    for version in versions:
        min_version = compare_version(min_version, version.groups()[0])

    return min_version

def compare_version(version_1, version_2):
    """
        compare version
    """
    v1 = version_1.split('.')
    v2 = version_2.split('.')
    if int(v1[1]) > int(v2[1]):
        return version_1
    elif int(v1[1]) == int(v2[1]) and int(v1[2]) > int(v2[2]):
        return version_1
    else:
        return version_2

class SimplifiedSlither(
    SlitherCore
):
    def __init__(self, target: Union[str, CryticCompile], **kwargs) -> None:
        super().__init__()

        self.taint_analyse_to_dots: list[str] = []
        self.snippets: list[str] = []
        self.granularity = kwargs.get("granularity", 'function')
        self.no_fail = kwargs.get("no_fail", False)
        self._parsers: List[SlitherCompilationUnitSolc] = []
        try:
            if isinstance(target, CryticCompile):
                crytic_compile = target
            else:
                crytic_compile = CryticCompile(target, **kwargs)
                
            self._crytic_compile = crytic_compile
            
        except InvalidCompilation as e:
            # pylint: disable=raise-missing-from
            raise SlitherError(f"Invalid compilation: \n{str(e)}")
        
        for compilation_unit in crytic_compile.compilation_units.values():
            compilation_unit_slither = SlitherCompilationUnit(self, compilation_unit)
            self._compilation_units.append(compilation_unit_slither)

            if compilation_unit_slither.is_vyper:
                vyper_parser = VyperCompilationUnit(compilation_unit_slither)
                for path, ast in compilation_unit.asts.items():
                    ast_nodes = parse(ast["ast"])
                    vyper_parser.parse_module(ast_nodes, path)
                    
                self._parsers.append(vyper_parser)
            else:
                # Solidity specific
                assert compilation_unit_slither.is_solidity
                sol_parser = SlitherCompilationUnitSolc(compilation_unit_slither)
                self._parsers.append(sol_parser)
                for path, ast in compilation_unit.asts.items():
                    sol_parser.parse_top_level_items(ast, path)
                    self.add_source_code(path)

                for contract in sol_parser._underlying_contract_to_parser:
                    if contract.name.startswith("SlitherInternalTopLevelContract"):
                        raise SlitherError(
                            # region multi-line-string
                            """Your codebase has a contract named 'SlitherInternalTopLevelContract'.
                            Please rename it, this name is reserved for Slither's internals"""
                            # endregion multi-line
                        )
                        
                    sol_parser._contracts_by_id[contract.id] = contract
                    sol_parser._compilation_unit.contracts.append(contract)

                _update_file_scopes(sol_parser)

        self._init_parsing_and_analyses()

    def _init_parsing_and_analyses(self) -> None:

        for parser in self._parsers:
            try:
                parser.parse_contracts()
                
            except Exception as e:
                if self.no_fail:
                    continue
                
                raise e

        for parser in self._parsers:
            try:
                if not parser._parsed:
                    raise SlitherException("Parse the contract before running analyses")
                
                parser._convert_to_slithir()
                taint = TaintPropagation(parser.compilation_unit, self.granularity)
                self.taint_analyse_to_dots.append(taint.dot)
                self.snippets.append(taint.snippet)
                parser._analyzed = True

            except Exception as e:
                if self.no_fail:
                    continue
                
                raise e
