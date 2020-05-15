import json
import os

import pandas as pd


class Codex(object):

    # Available language codes
    CODES = ['ar', 'de', 'en', 'es', 'ru', 'zh']
    SIZES = ['s', 'm', 'l']

    def __init__(self, code='en', size='s',
                 codex_base=os.path.dirname(os.path.realpath(__file__))):
        """
        :param code: one of Codex.CODES
        :param size: one of Codex.SIZES
        :param codex_base: path to codex data
        """
        if code not in Codex.CODES:
            raise ValueError('Language code {} not supported'.format(
                code))
        if size not in Codex.SIZES:
            raise ValueError('Size {} not recognized'.format(
                size))

        self.code = code
        self.size = size
        self.codex_base = codex_base

        self.entities_ = {}
        self.relations_ = {}
        self.entity_types_ = {}
        self.type_labels_ = {}

        self.train_, self.valid_, self.test_ = [
            pd.DataFrame() for _ in range(3)
        ]

        self.valid_neg_, self.test_neg_ = [
            pd.DataFrame() for _ in range(2)
        ]

    def entities(self):
        """Get all entities as a set"""
        triples = self.triples()
        return set(pd.concat((triples['head'], triples['tail'])))

    def relations(self):
        """Get all relations as a set"""
        return set(self.triples()['relation'])

    def entity_label(self, eid):
        """Get the label of the specified entity"""
        entities = self._load_entities()
        return entities[eid]['label']

    def entity_description(self, eid):
        """Get the Wikidata description of the specified entity"""
        entities = self._load_entities()
        return entities[eid]['description']

    def entity_types(self, eid):
        """Get all the entity types of this entity as
        as list; note that types are Wikidata IDs"""
        types = self._load_entity_types()
        return types[eid]

    def entity_extract(self, eid):
        """Get the Wikipedia intro extract for this entity"""
        fname = os.path.join(
            self.codex_base, 'entities', self.code,
            'extracts', '{}.txt'.format(eid))
        if os.path.exists(fname):
            with open(fname) as f:
                return ''.join(f.readlines())
        return ''

    def relation_label(self, rid):
        """Get the label of this relation"""
        relations = self._load_relations()
        return relations[rid]['label']

    def relation_description(self, rid):
        """Get the Wikidata description of this relation"""
        relations = self._load_relations()
        return relations[rid]['description']

    def entity_type_label(self, type_id):
        """Get the label of this entity type"""
        type_labels = self._load_entity_type_labels()
        return type_labels[type_id]['label']

    def entity_type_description(self, type_id):
        """Get the Wikidata description of this entity type"""
        type_labels = self._load_entity_type_labels()
        return type_labels[type_id]['description']

    def entity_type_extract(self, type_id):
        """Get the Wikipedia intro extract for this entity type"""
        fname = os.path.join(
            self.codex_base, 'types', self.code,
            'extracts', '{}.txt'.format(type_id))
        if os.path.exists(fname):
            with open(fname) as f:
                return ''.join(f.readlines())
        return ''

    def triples(self):
        """Get ALL triples in the dataset as a pandas DataFrame
        with columns ['head', 'relation', 'tail']"""
        return pd.concat(
            (self._load_train(), self._load_valid(), self._load_test())
        )

    def split(self, split):
        """
        :param split: one of train, test, or valid
        :return: all triples in the specified split as a pandas DataFrame
            with columns ['head', 'relation', 'tail']
        """
        if split == 'train':
            return self._load_train()
        elif split == 'valid':
            return self._load_valid()
        elif split == 'test':
            return self._load_test()
        else:
            raise ValueError('Split {} not recognized'.format(split))

    def negative_split(self, split):
        """
        :param split: one of valid or test
        :return: negative triples in the split as a pandas DataFrame
            Only supported for CoDEx-S
        """
        if self.size != 's':
            raise ValueError('Negatives only supported for CoDEx-S')
        if split == 'valid':
            return self._load_valid_neg()
        elif split == 'test':
            return self._load_test_neg()
        else:
            raise ValueError('Split {} not recognized for negatives'.format(
                split))

    # Data loading utilities -----------------------------------------

    def _load_entities(self):
        if not len(self.entities_):
            self.entities_ = json.load(
                open(os.path.join(
                    self.codex_base,
                    'entities',
                    self.code,
                    'entities.json')))
        return self.entities_

    def _load_relations(self):
        if not len(self.relations_):
            self.relations_ = json.load(
                open(os.path.join(
                    self.codex_base,
                    'relations',
                    self.code,
                    'relations.json')))
        return self.relations_

    def _load_entity_types(self):
        if not len(self.entity_types_):
            self.entity_types_ = json.load(
                open(os.path.join(
                    self.codex_base,
                    'types',
                    'entity2types.json')))
        return self.entity_types_

    def _load_entity_type_labels(self):
        if not len(self.type_labels_):
            self.type_labels_ = json.load(
                open(os.path.join(
                    self.codex_base,
                    'types',
                    self.code,
                    'types.json')))
        return self.type_labels_

    def _load_train(self):
        if not len(self.train_):
            self.train_ = self._load_triples('train')
            columns = ['head', 'relation', 'tail']
            self.train_.columns = columns
        return self.train_

    def _load_valid(self):
        if not len(self.valid_):
            self.valid_ = self._load_triples('valid')
            columns = ['head', 'relation', 'tail']
            self.valid_.columns = columns
        return self.valid_

    def _load_valid_neg(self):
        if not len(self.valid_neg_):
            self.valid_neg_ = self._load_triples('valid_neg')
            columns = ['head', 'relation', 'tail']
            self.valid_neg_.columns = columns
        return self.valid_neg_

    def _load_test(self):
        if not len(self.test_):
            self.test_ = self._load_triples('test')
            columns = ['head', 'relation', 'tail']
            self.test_.columns = columns
        return self.test_

    def _load_test_neg(self):
        if not len(self.test_neg_):
            self.test_neg_ = self._load_triples('test_neg')
            columns = ['head', 'relation', 'tail']
            self.test_neg_.columns = columns
        return self.test_neg_

    def _load_triples(self, split):
        return pd.read_csv(
            os.path.join(
                self.codex_base,
                'triples',
                'codex-{}'.format(self.size),
                '{}.txt'.format(split)),
            sep='\t', header=None)
