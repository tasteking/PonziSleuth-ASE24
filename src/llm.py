"""
    Interact with OpenAI and Ollama
"""

from openai import OpenAI
import os
import json
import signal
import requests

def timeout_handler(signum, frame):
    raise TimeoutError('Model doesn\'t response for a while')

signal.signal(signal.SIGALRM, timeout_handler)

class Sleuth():
    def __init__(self, dot: str, snippet: str, model: str, temperature, cot: bool):
        self.model = model
        self.temerature = temperature
        self.dot = dot
        self.cot = cot
        self.snippet = snippet
        
        if 'gpt' in self.model:
            self.target = 'gpt'

        else:
            self.target = self.model
        
        with open(os.path.join(os.getcwd(), 'prompt', 'prompts.json')) as f:
            self.prompt_dict = json.load(f)[self.target]
        
        self.context = [self.prompt_dict['system']]
        self.json = {
            'system': self.prompt_dict['system']['content'],
            'model': model,
            'options': {
                'temperature': temperature
            },
            'stream': False
        }
        print(f'{model} detecting...')
    
    def analyse(self):
        if self.cot:
            if self.target == 'gpt':
                return self._openai()
            else:
                return self._ollama()

        else:
            if self.target == 'gpt':
                return self.openai()
            else:
                return self.ollama()

    def _openai(self):
        self.client = OpenAI()
        prompt_tks = completion_tks = total_tks = 0
        self.prompt_dict['analysis']['content'] = self.prompt_dict['ponzi']['content'] + self.prompt_dict['analysis']['content'] + self.snippet + '\n' + self.prompt_dict['abalation']['content']
        self.context.append(self.prompt_dict['analysis'])
        
        try:
            signal.alarm(100)
            response = self.client.chat.completions.create(
                model = self.model,
                messages = self.context,
                temperature = self.temerature,
                response_format={'type':'json_object'}
            )
            prompt_tks += response.usage.prompt_tokens
            completion_tks += response.usage.completion_tokens
            total_tks += response.usage.total_tokens

        except Exception as e:
            signal.alarm(0)
            raise e
        
        finally:
            signal.alarm(0)

        decision = self.parse_gpt(response.choices[0].message.content)
        print(f'< Audit result: [ {decision} ] >')
        return decision, self.prompt_dict['analysis']['content'], prompt_tks, completion_tks#, total_tks

    def _ollama(self):
        self.json['prompt'] = self.prompt_dict['analysis']['content'] + self.snippet + '\n' + self.prompt_dict['abalation']['content']
        self.json['format'] = 'json'
        
        try:
            signal.alarm(100)
            response = requests.post(
                "http://localhost:11434/api/generate",
                json=self.json
            )

        except Exception as e:
            signal.alarm(0)
            raise e

        finally:
            signal.alarm(0)

        decision= self.parse_ollama(response.json()['response'])
        print(f"< Audit result: [ {decision} ] >")
        
        return decision, self.json['prompt'], 0, 0

    def openai(self):
        self.client = OpenAI()
        prompt_tks = completion_tks = total_tks = 0
        if self.dot != '':
            self.prompt_dict['analysis']['content'] = self.prompt_dict['ponzi']['content'] + self.prompt_dict['analysis']['content'] + self.snippet + '\n' + self.prompt_dict['graph']['content'] + self.dot + '\n' + self.prompt_dict['chain_of_thought']['content']
        
        else:
            self.prompt_dict['analysis']['content'] = self.prompt_dict['ponzi']['content'] + self.prompt_dict['analysis']['content'] + self.snippet + '\n' + self.prompt_dict['chain_of_thought']['content']
        
        self.context.append(self.prompt_dict['analysis'])
        
        try:
            signal.alarm(100)
            response = self.client.chat.completions.create(
                model = self.model,
                messages = self.context,
                temperature = self.temerature
            )
            prompt_tks = response.usage.prompt_tokens
            completion_tks = response.usage.completion_tokens
            total_tks = response.usage.total_tokens

        except Exception as e:
            signal.alarm(0)
            raise e

        finally:
            signal.alarm(0)

        # role = response.choices[0].message.role
        analysis = response.choices[0].message.content
        self.context[1]['content'] = self.context[1]['content'] + '\n' + analysis + '\n' + self.prompt_dict['decision']['content']
        # self.context[1]['content'] = analysis + '\n' + self.prompt_dict['decision']['content']
        # print(f"{self.context[1]['content']}")
        
        try:
            signal.alarm(100)
            response = self.client.chat.completions.create(
                model = self.model,
                messages = self.context,
                temperature = self.temerature,
                response_format={'type':'json_object'}
            )
            prompt_tks += response.usage.prompt_tokens
            completion_tks += response.usage.completion_tokens
            total_tks += response.usage.total_tokens

        except Exception as e:
            signal.alarm(0)
            raise e
        
        finally:
            signal.alarm(0)

        decision = self.parse_gpt(response.choices[0].message.content)
        print(f'< Audit result: [ {decision} ] >')
        return decision, analysis, prompt_tks, completion_tks#, total_tks

    def ollama(self):
        self.json['prompt'] = self.prompt_dict['analysis']['content'] + self.snippet + '\n' + self.prompt_dict['chain_of_thought']['graph'] + self.dot + '\n' + self.prompt_dict['chain_of_thought']['explain'] + self.prompt_dict['chain_of_thought']['content']
        # print(f"{self.json['prompt']}")
        
        try:
            signal.alarm(100)
            response = requests.post(
                "http://localhost:11434/api/generate",
                json=self.json
            )

        except Exception as e:
            signal.alarm(0)
            raise e

        finally:
            signal.alarm(0)
        
        analysis = response.json()['response']
        # print(f"Assistant:\n{analysis}")
        # self.json['prompt'] = self.json['prompt'] + '\n' + analysis + '\n' + self.prompt_dict['decision']['content']
        self.json['prompt'] = self.prompt_dict['decision']['content']
        self.json['context'] = response.json()['context']
        self.json['format'] = 'json'
        # print(f"{self.json['prompt']}")
        
        try:
            signal.alarm(100)
            response = requests.post(
                "http://localhost:11434/api/generate",
                json=self.json
            )

        except Exception as e:
            signal.alarm(0)
            raise e

        finally:
            signal.alarm(0)

        # print(response.json()['response'])
        decision= self.parse_ollama(response.json()['response'])
        print(f"< Audit result: [ {decision} ] >")
        
        return decision, analysis, 0, 0

    def parse_gpt(self, response):
        if isinstance(response, dict):
            if 'decision' in response:
                return response['decision']
            elif 'Decision' in response:
                return response['Decision']
            else:
                if response != {}:
                    return list(response.values())[0]
                else:
                    return 'None'

        elif isinstance(response, str):
            try:
                response_dict = json.loads(response)
                if 'decision' in response_dict:
                    return response_dict['decision']
                elif 'Decision' in response_dict:
                    return response_dict['Decision']
                else:
                    if response_dict != {}:
                        return list(response_dict.values())[0]
                    else:
                        return 'None'

            except:
                try:
                    response_dict = eval(response.replace('\n', ''))
                    if 'decision' in response_dict:
                        return response_dict['decision']
                    elif 'Decision' in response_dict:
                        return response_dict['Decision']
                    else:
                        if response_dict != {}:
                            return list(response_dict.values())[0]
                        else:
                            return 'None'

                except:
                    return response.replace('\n', '')

        else:
            try:
                if 'decision' in response:
                    return response['decision']
                
                elif 'Decision' in response:
                    return response['Decision']
                
                else:
                    return response.replace('\n', '')

            except:
                return response.replace('\n', '')
    
    def parse_ollama(self, response):
        if isinstance(response, dict):
            if 'decision' in response:
                return response['decision']
            elif 'Decision' in response:
                return response['Decision']
            else:
                if response != {}:
                    return list(response.values())[0]
                else:
                    return 'None'

        elif isinstance(response, str):
            try:
                response_dict = json.loads(response)
                if 'decision' in response_dict:
                    return response_dict['decision']
                elif 'Decision' in response_dict:
                    return response_dict['Decision']
                else:
                    if response_dict != {}:
                        return list(response_dict.values())[0]
                    else:
                        return 'None'

            except:
                try:
                    response_dict = eval(response.replace('\n', ''))
                    if 'decision' in response_dict:
                        return response_dict['decision']
                    elif 'Decision' in response_dict:
                        return response_dict['Decision']
                    else:
                        if response_dict != {}:
                            return list(response_dict.values())[0]
                        else:
                            return 'None'

                except:
                    return response.replace('\n', '')

        else:
            try:
                if 'decision' in response:
                    return response['decision']
                
                elif 'Decision' in response:
                    return response['Decision']
                
                else:
                    return response.replace('\n', '')

            except:
                return response.replace('\n', '')
