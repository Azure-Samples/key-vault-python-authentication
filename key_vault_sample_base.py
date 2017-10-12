# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
import sys
import os
import time
import json
import inspect
import traceback
import azure.mgmt.keyvault.models
import azure.keyvault.models
from random import Random
from key_vault_sample_config import KeyVaultSampleConfig
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.keyvault import KeyVaultManagementClient
from azure.keyvault import KeyVaultClient, KeyVaultAuthentication
from msrest.exceptions import ClientRequestError
from msrestazure.azure_active_directory import ServicePrincipalCredentials
from msrest.paging import Paged
from msrest.serialization import Serializer
from azure.mgmt.keyvault.models import AccessPolicyEntry, VaultProperties, Sku, KeyPermissions, SecretPermissions, \
    CertificatePermissions, Permissions, VaultCreateOrUpdateParameters

SECRET_PERMISSIONS_ALL = [perm.value for perm in SecretPermissions]
KEY_PERMISSIONS_ALL = [perm.value for perm in KeyPermissions]
CERTIFICATE_PERMISSIONS_ALL = [perm.value for perm in CertificatePermissions]

_rand = Random()

def get_name(base):
    """
    randomly builds a unique name for an entity beginning with the specified base 
    :param base: the prefix for the generated name
    :return: a random unique name
    """
    name = '{}-{}-{}'.format(base, _rand.choice(adjectives), _rand.choice(nouns))
    if len(name) < 22:
        name += '-'
        for i in range(min(5, 23 - len(name))):
            name += str(_rand.choice(range(10)))
    return name

def keyvaultsample(f):
    """
    decorator function for marking key vault sample methods
    """
    def wrapper(self):
        try:
            print('--------------------------------------------------------------------')
            print('RUNNING: {}'.format(f.__name__))
            print('--------------------------------------------------------------------')
            self.setup_sample()
            f(self)
        except Exception as e:
            print('ERROR: running sample failed with raised exception:')
            traceback.print_exception(type(e), e, getattr(e, '__traceback__', None))
    wrapper.__name__ = f.__name__
    wrapper.__doc__ = f.__doc__
    wrapper.kv_sample = True
    return wrapper

def run_all_samples(samples):
    """
    runs all sample methods (methods marked with @keyvaultsample) on the specified samples objects,
    filtering to any sample methods specified on the command line
    :param samples: a list of sample objects
    :return: None 
    """
    requested_samples = sys.argv[1:]
    sample_funcs = []

    for s in samples:
        class_samples = {name: func for name, func in s.samples if not requested_samples or name in requested_samples}
        if class_samples:
            mod_name = os.path.basename(sys.modules[s.__module__].__file__)
            print('\n{}:\n'.format(mod_name))
            for name, func in class_samples.items():
                print('\t{} -- {}'.format(name, func.__doc__.strip()))
                sample_funcs.append(func)

    for f in sample_funcs:
        f()


class KeyVaultSampleBase(object):
    """Base class for Key Vault samples, provides common functionality needed across Key Vault sample code

    :ivar config: Azure subscription id for the user intending to run the sample
    :vartype config: :class: `KeyVaultSampleConfig`q
    
    :ivar credentials: Azure Active Directory credentials used to authenticate with Azure services
    :vartype credentials: :class: `ServicePrincipalCredentials 
     <msrestazure.azure_active_directory.ServicePrincipalCredentials>`
    
    :ivar keyvault_data_client: Key Vault data client used for interacting with key vaults 
    :vartype keyvault_data_client: :class: `KeyVaultClient <azure.keyvault.KeyVaultClient>`
    
    :ivar keyvault_mgmt_client: Key Vault management client used for creating and managing key vaults 
    :vartype keyvault_mgmt_client:  :class: `KeyVaultManagementClient <azure.mgmt.keyvault.KeyVaultManagementClient>`
    
    :ivar resource_mgmt_client: Azure resource management client used for managing azure resources, access, and groups 
    :vartype resource_mgmt_client:  :class: `ResourceManagementClient <azure.mgmt.resource.ResourceManagementClient>`
    """
    def __init__(self):
        self.config = KeyVaultSampleConfig()
        self.credentials = None
        self.keyvault_data_client = None
        self.keyvault_mgmt_client = None
        self.resource_mgmt_client = None
        self._setup_complete = False
        self.samples = {(name, m) for name, m in inspect.getmembers(self) if getattr(m, 'kv_sample', False)}
        models = {}
        models.update({k: v for k, v in azure.keyvault.models.__dict__.items() if isinstance(v, type)})
        models.update({k: v for k, v in azure.mgmt.keyvault.models.__dict__.items() if isinstance(v, type)})
        self._serializer = Serializer(models)

    def setup_sample(self):
        """
        Provides common setup for Key Vault samples, such as creating rest clients, creating a sample resource group
        if needed, and ensuring proper access for the service principal.
         
        :return: None 
        """
        if not self._setup_complete:
            self.mgmt_creds = ServicePrincipalCredentials(client_id=self.config.client_id, secret=self.config.client_secret,
                                                          tenant=self.config.tenant_id)
            self.data_creds = ServicePrincipalCredentials(client_id=self.config.client_id, secret=self.config.client_secret,
                                                          tenant=self.config.tenant_id)
            self.resource_mgmt_client = ResourceManagementClient(self.mgmt_creds, self.config.subscription_id)

            # ensure the service principle has key vault as a valid provider
            self.resource_mgmt_client.providers.register('Microsoft.KeyVault')

            # ensure the intended resource group exists
            self.resource_mgmt_client.resource_groups.create_or_update(self.config.group_name, {'location': self.config.location})

            self.keyvault_mgmt_client = KeyVaultManagementClient(self.mgmt_creds, self.config.subscription_id)

            self.keyvault_data_client = KeyVaultClient(self.data_creds)

            self._setup_complete = True


    def create_vault(self):
        """
        Creates a new key vault with a unique name, granting full permissions to the current credentials
        :return: a newly created key vault
        :rtype: :class:`Vault <azure.keyvault.generated.models.Vault>`
        """
        vault_name = get_name('vault')

        # setup vault permissions for the access policy for the sample service principle
        permissions = Permissions()
        permissions.keys = KEY_PERMISSIONS_ALL
        permissions.secrets = SECRET_PERMISSIONS_ALL
        permissions.certificates = CERTIFICATE_PERMISSIONS_ALL
        
        policy = AccessPolicyEntry(self.config.tenant_id, self.config.client_oid, permissions)

        properties = VaultProperties(self.config.tenant_id, Sku(name='standard'), access_policies=[policy])

        parameters = VaultCreateOrUpdateParameters(self.config.location, properties)
        parameters.properties.enabled_for_deployment = True
        parameters.properties.enabled_for_disk_encryption = True
        parameters.properties.enabled_for_template_deployment = True

        print('creating vault {}'.format(vault_name))

        vault = self.keyvault_mgmt_client.vaults.create_or_update(self.config.group_name, vault_name, parameters)

        # wait for vault DNS entry to be created
        # see issue: https://github.com/Azure/azure-sdk-for-python/issues/1172
        self._poll_for_vault_connection(vault.properties.vault_uri)

        print('created vault {} {}'.format(vault_name, vault.properties.vault_uri))

        return vault

    def _poll_for_vault_connection(self, vault_uri, retry_wait=10, max_retries=4):
        """
        polls the data client 'get_secrets' method until a 200 response is received indicating the the vault
        is available for data plane requests
        """
        last_error = None
        for x in range(max_retries - 1):
            try:
                # sleep first to avoid improper DNS caching
                time.sleep(retry_wait)
                self.keyvault_data_client.get_secrets(vault_uri)
                return
            except ClientRequestError as e:
                print('vault connection not available')
                last_error = e
        raise last_error

    def _serialize(self, obj):
        if isinstance(obj, Paged):
            serialized = [self._serialize(i) for i in list(obj)]
        else:
            serialized = self._serializer.body(obj, type(obj).__name__)
        return json.dumps(serialized, indent=4, separators=(',', ': '))


adjectives = ['able', 'acid', 'adept', 'aged', 'agile', 'ajar', 'alert', 'alive', 'all', 'ample',
              'angry', 'antsy', 'any', 'apt', 'arid', 'awake', 'aware', 'back', 'bad', 'baggy',
              'bare', 'basic', 'batty', 'beefy', 'bent', 'best', 'big', 'black', 'bland', 'blank',
              'bleak', 'blind', 'blond', 'blue', 'bogus', 'bold', 'bony', 'bossy', 'both', 'bowed',
              'brave', 'brief', 'brisk', 'brown', 'bulky', 'bumpy', 'burly', 'busy', 'cagey', 'calm',
              'cheap', 'chief', 'clean', 'close', 'cold', 'cool', 'corny', 'crazy', 'crisp', 'cruel',
              'curvy', 'cut', 'cute', 'damp', 'dark', 'dead', 'dear', 'deep', 'dense', 'dim',
              'dirty', 'dizzy', 'dopey', 'drab', 'dry', 'dual', 'dull', 'dull', 'each', 'eager',
              'early', 'easy', 'elite', 'empty', 'equal', 'even', 'every', 'evil', 'fair', 'fake',
              'far', 'fast', 'fat', 'few', 'fine', 'firm', 'five', 'flat', 'fond', 'four',
              'free', 'full', 'fuzzy', 'gamy', 'glib', 'glum', 'good', 'gray', 'grey', 'grim',
              'half', 'half', 'hard', 'high', 'hot', 'huge', 'hurt', 'icky', 'icy', 'ideal',
              'ideal', 'idle', 'ill', 'itchy', 'jaded', 'joint', 'juicy', 'jumbo', 'jumpy', 'jumpy',
              'keen', 'key', 'kind', 'known', 'kooky', 'kosher', 'lame', 'lame', 'lanky', 'large',
              'last', 'late', 'lazy', 'leafy', 'lean', 'left', 'legal', 'lewd', 'light', 'like',
              'limp', 'lined', 'live', 'livid', 'lone', 'long', 'loose', 'lost', 'loud', 'low',
              'loyal', 'lumpy', 'lush', 'mad', 'major', 'male', 'many', 'mealy', 'mean', 'meaty',
              'meek', 'mere', 'merry', 'messy', 'mild', 'milky', 'minor', 'minty', 'misty', 'mixed',
              'moist', 'moody', 'moral', 'muddy', 'murky', 'mushy', 'musty', 'mute', 'muted', 'naive',
              'nasty', 'near', 'neat', 'new', 'next', 'nice', 'nice', 'nine', 'nippy', 'nosy',
              'noted', 'novel', 'null', 'numb', 'nutty', 'obese', 'odd', 'oily', 'old', 'one',
              'only', 'open', 'other', 'our', 'oval', 'pale', 'past', 'perky', 'pesky', 'petty',
              'phony', 'pink', 'plump', 'plush', 'poor', 'posh', 'prime', 'prize', 'proud', 'puny',
              'pure', 'pushy', 'pushy', 'quick', 'quiet', 'rainy', 'rapid', 'rare', 'rash', 'raw',
              'ready', 'real', 'red', 'regal', 'rich', 'right', 'rigid', 'ripe', 'rosy', 'rough',
              'rowdy', 'rude', 'runny', 'sad', 'safe', 'salty', 'same', 'sandy', 'sane', 'scaly',
              'shady', 'shaky', 'sharp', 'shiny', 'short', 'showy', 'shut', 'shy', 'sick', 'silky',
              'six', 'slim', 'slimy', 'slow', 'small', 'smart', 'smug', 'soft', 'solid', 'some',
              'sore', 'soupy', 'sour', 'sour', 'spicy', 'spiky', 'spry', 'staid', 'stale', 'stark',
              'steel', 'steep', 'stiff', 'stout', 'sunny', 'super', 'sweet', 'swift', 'tall', 'tame',
              'tan', 'tart', 'tasty', 'taut', 'teeny', 'ten', 'tepid', 'testy', 'that', 'these',
              'thick', 'thin', 'third', 'this', 'those', 'tidy', 'tiny', 'torn', 'total', 'tough',
              'trim', 'true', 'tubby', 'twin', 'two', 'ugly', 'unfit', 'upset', 'urban', 'used',
              'used', 'utter', 'vague', 'vain', 'valid', 'vapid', 'vast', 'vexed', 'vital', 'vivid',
              'wacky', 'wan', 'warm', 'wary', 'wavy', 'weak', 'weary', 'wee', 'weepy', 'weird',
              'wet', 'which', 'white', 'whole', 'wide', 'wild', 'windy', 'wiry', 'wise', 'witty',
              'woozy', 'wordy', 'worn', 'worse', 'worst', 'wrong', 'wry', 'yummy', 'zany', 'zesty',
              'zonked']

nouns = ['abroad', 'abuse', 'access', 'act', 'action', 'active', 'actor', 'adult', 'advice', 'affair',
         'affect', 'age', 'agency', 'agent', 'air', 'alarm', 'amount', 'anger', 'angle', 'animal',
         'annual', 'answer', 'appeal', 'apple', 'area', 'arm', 'army', 'art', 'aside', 'ask',
         'aspect', 'assist', 'attack', 'author', 'award', 'baby', 'back', 'bad', 'bag', 'bake',
         'ball', 'band', 'bank', 'bar', 'base', 'basis', 'basket', 'bat', 'bath', 'battle',
         'beach', 'bear', 'beat', 'bed', 'beer', 'being', 'bell', 'belt', 'bench', 'bend',
         'bet', 'beyond', 'bid', 'big', 'bike', 'bill', 'bird', 'birth', 'bit', 'bite',
         'bitter', 'black', 'blame', 'blank', 'blind', 'block', 'blood', 'blow', 'blue', 'board',
         'boat', 'body', 'bone', 'bonus', 'book', 'boot', 'border', 'boss', 'bother', 'bottle',
         'bottom', 'bowl', 'box', 'boy', 'brain', 'branch', 'brave', 'bread', 'break', 'breast',
         'breath', 'brick', 'bridge', 'brief', 'broad', 'brown', 'brush', 'buddy', 'budget', 'bug',
         'bunch', 'burn', 'bus', 'button', 'buy', 'buyer', 'cable', 'cake', 'call', 'calm',
         'camera', 'camp', 'can', 'cancel', 'cancer', 'candle', 'candy', 'cap', 'car', 'card',
         'care', 'career', 'carpet', 'carry', 'case', 'cash', 'cat', 'catch', 'cause', 'cell',
         'chain', 'chair', 'chance', 'change', 'charge', 'chart', 'check', 'cheek', 'chest', 'child',
         'chip', 'choice', 'church', 'city', 'claim', 'class', 'clerk', 'click', 'client', 'clock',
         'closet', 'cloud', 'club', 'clue', 'coach', 'coast', 'coat', 'code', 'coffee', 'cold',
         'collar', 'common', 'cook', 'cookie', 'copy', 'corner', 'cost', 'count', 'county', 'couple',
         'course', 'court', 'cousin', 'cover', 'cow', 'crack', 'craft', 'crash', 'crazy', 'cream',
         'credit', 'crew', 'cross', 'cry', 'cup', 'curve', 'cut', 'cycle', 'dad', 'damage',
         'dance', 'dare', 'dark', 'data', 'date', 'day', 'dead', 'deal', 'dealer', 'dear',
         'death', 'debate', 'debt', 'deep', 'degree', 'delay', 'demand', 'depth', 'design', 'desire',
         'desk', 'detail', 'device', 'devil', 'diet', 'dig', 'dinner', 'dirt', 'dish', 'disk',
         'divide', 'doctor', 'dog', 'door', 'dot', 'double', 'doubt', 'draft', 'drag', 'drama',
         'draw', 'drawer', 'dream', 'dress', 'drink', 'drive', 'driver', 'drop', 'drunk', 'due',
         'dump', 'dust', 'duty', 'ear', 'earth', 'ease', 'east', 'eat', 'edge', 'editor',
         'effect', 'effort', 'egg', 'employ', 'end', 'energy', 'engine', 'entry', 'equal', 'error',
         'escape', 'essay', 'estate', 'event', 'exam', 'excuse', 'exit', 'expert', 'extent', 'eye',
         'face', 'fact', 'factor', 'fail', 'fall', 'family', 'fan', 'farm', 'farmer', 'fat',
         'father', 'fault', 'fear', 'fee', 'feed', 'feel', 'female', 'few', 'field', 'fight',
         'figure', 'file', 'fill', 'film', 'final', 'finger', 'finish', 'fire', 'fish', 'fix',
         'flight', 'floor', 'flow', 'flower', 'fly', 'focus', 'fold', 'food', 'foot', 'force',
         'form', 'formal', 'frame', 'friend', 'front', 'fruit', 'fuel', 'fun', 'funny', 'future',
         'gain', 'game', 'gap', 'garage', 'garden', 'gas', 'gate', 'gather', 'gear', 'gene',
         'gift', 'girl', 'give', 'glad', 'glass', 'glove', 'goal', 'god', 'gold', 'golf',
         'good', 'grab', 'grade', 'grand', 'grass', 'great', 'green', 'ground', 'group', 'growth',
         'guard', 'guess', 'guest', 'guide', 'guitar', 'guy', 'habit', 'hair', 'half', 'hall',
         'hand', 'handle', 'hang', 'harm', 'hat', 'hate', 'head', 'health', 'heart', 'heat',
         'heavy', 'height', 'hell', 'hello', 'help', 'hide', 'high', 'hire', 'hit', 'hold',
         'hole', 'home', 'honey', 'hook', 'hope', 'horror', 'horse', 'host', 'hotel', 'hour',
         'house', 'human', 'hunt', 'hurry', 'hurt', 'ice', 'idea', 'ideal', 'image', 'impact',
         'income', 'injury', 'insect', 'inside', 'invite', 'iron', 'island', 'issue', 'item', 'jacket',
         'job', 'join', 'joint', 'joke', 'judge', 'juice', 'jump', 'junior', 'jury', 'keep',
         'key', 'kick', 'kid', 'kill', 'kind', 'king', 'kiss', 'knee', 'knife', 'lab',
         'lack', 'ladder', 'lady', 'lake', 'land', 'laugh', 'law', 'lawyer', 'lay', 'layer',
         'lead', 'leader', 'league', 'leave', 'leg', 'length', 'lesson', 'let', 'letter', 'level',
         'lie', 'life', 'lift', 'light', 'limit', 'line', 'link', 'lip', 'list', 'listen',
         'living', 'load', 'loan', 'local', 'lock', 'log', 'long', 'look', 'loss', 'love',
         'low', 'luck', 'lunch', 'mail', 'main', 'major', 'make', 'male', 'mall', 'man',
         'manner', 'many', 'map', 'march', 'mark', 'market', 'master', 'match', 'mate', 'math',
         'matter', 'maybe', 'meal', 'meat', 'media', 'medium', 'meet', 'member', 'memory', 'menu',
         'mess', 'metal', 'method', 'middle', 'might', 'milk', 'mind', 'mine', 'minor', 'minute',
         'mirror', 'miss', 'mix', 'mobile', 'mode', 'model', 'mom', 'moment', 'money', 'month',
         'mood', 'most', 'mother', 'motor', 'mouse', 'mouth', 'move', 'movie', 'mud', 'muscle',
         'music', 'nail', 'name', 'nasty', 'nation', 'native', 'nature', 'neat', 'neck', 'nerve',
         'net', 'news', 'night', 'nobody', 'noise', 'normal', 'north', 'nose', 'note', 'notice',
         'novel', 'number', 'nurse', 'object', 'offer', 'office', 'oil', 'one', 'option', 'orange',
         'order', 'other', 'oven', 'owner', 'pace', 'pack', 'page', 'pain', 'paint', 'pair',
         'panic', 'paper', 'parent', 'park', 'part', 'party', 'pass', 'past', 'path', 'pause',
         'pay', 'peace', 'peak', 'pen', 'people', 'period', 'permit', 'person', 'phase', 'phone',
         'photo', 'phrase', 'piano', 'pick', 'pie', 'piece', 'pin', 'pipe', 'pitch', 'pizza',
         'place', 'plan', 'plane', 'plant', 'plate', 'play', 'player', 'plenty', 'poem', 'poet',
         'poetry', 'point', 'police', 'policy', 'pool', 'pop', 'post', 'pot', 'potato', 'pound',
         'power', 'press', 'price', 'pride', 'priest', 'print', 'prior', 'prize', 'profit', 'prompt',
         'proof', 'public', 'pull', 'punch', 'purple', 'push', 'put', 'queen', 'quiet', 'quit',
         'quote', 'race', 'radio', 'rain', 'raise', 'range', 'rate', 'ratio', 'raw', 'reach',
         'read', 'reason', 'recipe', 'record', 'red', 'refuse', 'region', 'regret', 'relief', 'remote',
         'remove', 'rent', 'repair', 'repeat', 'reply', 'report', 'resist', 'resort', 'rest', 'result',
         'return', 'reveal', 'review', 'reward', 'rice', 'rich', 'ride', 'ring', 'rip', 'rise',
         'risk', 'river', 'road', 'rock', 'role', 'roll', 'roof', 'room', 'rope', 'rough',
         'round', 'row', 'royal', 'rub', 'ruin', 'rule', 'run', 'rush', 'sad', 'safe',
         'safety', 'sail', 'salad', 'salary', 'sale', 'salt', 'sample', 'sand', 'save', 'scale',
         'scene', 'scheme', 'school', 'score', 'screen', 'screw', 'script', 'sea', 'search', 'season',
         'seat', 'second', 'secret', 'sector', 'self', 'sell', 'senior', 'sense', 'series', 'serve',
         'set', 'sex', 'shake', 'shame', 'shape', 'share', 'she', 'shift', 'shine', 'ship',
         'shirt', 'shock', 'shoe', 'shoot', 'shop', 'shot', 'show', 'shower', 'sick', 'side',
         'sign', 'signal', 'silly', 'silver', 'simple', 'sing', 'singer', 'single', 'sink', 'sir',
         'sister', 'site', 'size', 'skill', 'skin', 'skirt', 'sky', 'sleep', 'slice', 'slide',
         'slip', 'smell', 'smile', 'smoke', 'snow', 'sock', 'soft', 'soil', 'solid', 'son',
         'song', 'sort', 'sound', 'soup', 'source', 'south', 'space', 'spare', 'speech', 'speed',
         'spell', 'spend', 'spirit', 'spite', 'split', 'sport', 'spot', 'spray', 'spread', 'spring',
         'square', 'stable', 'staff', 'stage', 'stand', 'star', 'start', 'state', 'status', 'stay',
         'steak', 'steal', 'step', 'stick', 'still', 'stock', 'stop', 'store', 'storm', 'story',
         'strain', 'street', 'stress', 'strike', 'string', 'strip', 'stroke', 'studio', 'study', 'stuff',
         'stupid', 'style', 'suck', 'sugar', 'suit', 'summer', 'sun', 'survey', 'sweet', 'swim',
         'swing', 'switch', 'system', 'table', 'tackle', 'tale', 'talk', 'tank', 'tap', 'target',
         'task', 'taste', 'tax', 'tea', 'teach', 'team', 'tear', 'tell', 'tennis', 'term',
         'test', 'text', 'thanks', 'theme', 'theory', 'thing', 'throat', 'ticket', 'tie', 'till',
         'time', 'tip', 'title', 'today', 'toe', 'tone', 'tongue', 'tool', 'tooth', 'top',
         'topic', 'total', 'touch', 'tough', 'tour', 'towel', 'tower', 'town', 'track', 'trade',
         'train', 'trash', 'travel', 'treat', 'tree', 'trick', 'trip', 'truck', 'trust', 'truth',
         'try', 'tune', 'turn', 'twist', 'two', 'type', 'uncle', 'union', 'unique', 'unit',
         'upper', 'use', 'user', 'usual', 'value', 'vast', 'video', 'view', 'virus', 'visit',
         'visual', 'voice', 'volume', 'wait', 'wake', 'walk', 'wall', 'war', 'wash', 'watch',
         'water', 'wave', 'way', 'wealth', 'wear', 'web', 'week', 'weight', 'weird', 'west',
         'wheel', 'while', 'white', 'whole', 'wife', 'will', 'win', 'wind', 'window', 'wine',
         'wing', 'winner', 'winter', 'wish', 'woman', 'wonder', 'wood', 'word', 'work', 'worker',
         'world', 'worry', 'worth', 'wrap', 'writer', 'yard', 'year', 'yellow', 'you', 'young',
         'youth', 'zone']