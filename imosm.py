import pandas as pd

TRACE = True
# Maximum length of intended sequence
MAX_LENGTH = 10
# Minimum weight of intended sequence
MIN_WEIGHT = 2


class Interaction:
    """An interaction is a tuple (action, outcome) with a valence"""

    def __init__(self, _action, _outcome, _valence):
        self._action = _action
        self._outcome = _outcome
        self._valence = _valence
        self.weight = 10

    def get_action(self):
        """Return the action"""
        return self._action

    def get_actions(self):
        """Return the action as a string for compatibilty with CompositeInteraction"""
        return str(self._action)

    def get_decision(self):
        """Return the decision key"""
        return f"{self._action}"
        # return f"a{self._action}"

    def get_outcome(self):
        """Return the action"""
        return self._outcome

    def get_valence(self):
        """Return the action"""
        return self._valence

    def key(self):
        """ The key to find this interaction in the dictinary is the string '<action><outcome>'. """
        return f"{self._action}{self._outcome}"

    def pre_key(self):
        """Return the key. Used for compatibility with CompositeInteraction"""
        return ""  # self.key()

    def __str__(self):
        """ Print interaction in the form '<action><outcome:<valence>' for debug."""
        return f"{self._action}{self._outcome}:{self._valence}"

    def __eq__(self, other):
        """ Interactions are equal if they have the same key """
        if isinstance(other, self.__class__):
            return self.key() == other.key()
        else:
            return False

    def get_length(self):
        """The length of the sequence of this interaction"""
        return 1

    def increment(self, interaction, interactions):
        """Return the enacted interaction for compatibility with composite interactions"""
        return interaction

    def current(self):
        """Return itself for compatibility with composite interactions"""
        return self

    def sequence(self):
        """Return the key. Use for compatibility with composite interactions"""
        return self.key()

    def get_post_interactions(self):
        """Return the empty list for compatibility with composite interactions"""
        return []


class CompositeInteraction:
    """A composite interaction is a tuple (pre_interaction, post_interaction) and a weight"""
    def __init__(self, pre_interaction, post_interaction):
        self.pre_interaction = pre_interaction
        self.post_interaction = post_interaction
        self.weight = 1
        self._step = 1

    def get_decision(self):
        """Return the flatten sequence of intermediary primitive interactions terminated with the final decision"""
        return f"{self.pre_interaction.sequence()}{self.post_interaction.get_decision()}"

    def get_actions(self):
        """Return the flat sequence of the decisions of this interaction as a string"""
        return f"{self.pre_interaction.get_actions()}{self.post_interaction.get_actions()}"

    def get_valence(self):
        """Return the valence of the pre_interaction plus the valence of the post_interaction"""
        return self.pre_interaction.get_valence() + self.post_interaction.get_valence()

    def reinforce(self):
        """Increment the composite interaction's weight"""
        self.weight += 1

    def key(self):
        """ The key to find this interaction in the dictionary is the string '<pre_interaction><post_interaction>'. """
        return f"({self.pre_interaction.key()},{self.post_interaction.key()})"

    def pre_key(self):
        """Return the key of the pre_interaction"""
        return self.pre_interaction.key()

    def __str__(self):
        """ Print the interaction in the Newick tree format (pre_interaction, post_interaction: valence) """
        return f"({self.pre_interaction}, {self.post_interaction}: {self.weight})"

    def __eq__(self, other):
        """ Interactions are equal if they have the same pre and post interactions """
        if isinstance(other, self.__class__):
            return (self.pre_interaction == other.pre_interaction) and (self.post_interaction == other.post_interaction)
        else:
            return False

    def get_length(self):
        """Return the length of the number of primitive interactions in this composite interaction"""
        return self.pre_interaction.get_length() + self.post_interaction.get_length()

    def increment(self, interaction, interactions):
        """Increment the step of the appropriate sub-interaction.
        Return the enacted interaction if it is over, or None if it is ongoing."""
        # First step
        if self._step == 1:
            interaction = self.pre_interaction.increment(interaction, interactions)
            # Ongoing pre-interaction. Return None
            if interaction is None:
                return None
            # Pre-interaction succeeded. Increment the step and return None
            elif interaction == self.pre_interaction:
                self._step = 2
                return None
            # Pre-interaction failed. Reset the step and return the enacted interaction
            else:
                self._step = 1
                return interaction
        # Second step
        else:
            interaction = self.post_interaction.increment(interaction, interactions)
            # Ongoing post-interaction. Return None
            if interaction is None:
                return None
            # Post-interaction succeeded. Reset the step and return this interaction
            elif interaction == self.post_interaction:
                self._step = 1
                return self
            # Post-interaction failed. Reset the step and return the enacted interaction
            else:
                self._step = 1
                composite_interaction = CompositeInteraction(self.pre_interaction, interaction)
                if composite_interaction.key() not in interactions:
                    # Add the enacted composite interaction to memory
                    interactions[composite_interaction.key()] = composite_interaction
                    if TRACE:
                        print(f"Learning {composite_interaction}")
                    return composite_interaction
                else:
                    # Reinforce the existing composite interaction and return it
                    interactions[composite_interaction.key()].reinforce()
                    if TRACE:
                        print(f"Reinforcing {interactions[composite_interaction.key()]}")
                    return interactions[composite_interaction.key()]

    def current(self):
        """Return the current intended primitive interaction"""
        # Step 1: the current primitive interaction of the pre-interaction
        if self._step == 1:
            return self.pre_interaction.current()
        # Step 2: The current primitive interaction of the post-interaction
        else:
            return self.post_interaction.current()

    def sequence(self):
        """Return the flat sequence of primitive interactions of this composite interaction"""
        return f"{self.pre_interaction.sequence()}{self.post_interaction.sequence()}"

    def get_post_interactions(self):
        """Return the list of the hierarchy of the sub post_interactions"""
        return [self.post_interaction] + self.post_interaction.get_post_interactions()


class Agent:
    def __init__(self, _interactions):
        """ Initialize our agent """
        self._interactions = {interaction.key(): interaction for interaction in _interactions}
        self._primitive_intended_interaction = self._interactions["01"]  # See how to avoid this default
        self._intended_interaction = None

        # The context
        self._penultimate_interaction = None
        self._previous_interaction = None
        self._last_interaction = None
        self._penultimate_composite_interaction = None
        self._previous_composite_interaction = None
        self._last_composite_interaction = None

        # Prepare the dataframe of proposed interactions
        default_interactions = [interaction for interaction in _interactions if interaction.get_outcome() == 0]
        data = {'activated': [""] * len(default_interactions),
                'weight': [0] * len(default_interactions),
                'actions': [i.get_actions() for i in default_interactions],
                'intention': [i.key() for i in default_interactions],
                'valence': [i.get_valence() for i in default_interactions],
                'decision': [i.get_decision() for i in default_interactions],
                'length': [1] * len(default_interactions),
                'pre': [""] * len(default_interactions)}
        self._default_df = pd.DataFrame(data)
        self.proposed_df = None
        self.decision_df = None
        self.trace_record = {}
        self.enacted_length = 0

    def action(self, _outcome):
        """Implement the agent's policy"""
        # Trace the previous cycle
        primitive_enacted_interaction = self._interactions[
            f"{self._primitive_intended_interaction.get_action()}{_outcome}"]
        enaction_succeeded = primitive_enacted_interaction == self._primitive_intended_interaction
        self.enacted_length += enaction_succeeded
        self.trace_record = {
                "code": self._primitive_intended_interaction.get_action(),
                "prediction": self._primitive_intended_interaction.get_outcome(),
                "outcome": _outcome,
                "status": "success" if enaction_succeeded else "fail",
                "valence": primitive_enacted_interaction.get_valence(),
                "i_length": self._intended_interaction.get_length() if self._intended_interaction else 1,
                "e_length": self.enacted_length
        }
        # Follow up the enaction
        if self._intended_interaction is None:  # First interaction cycle
            enacted_interaction = primitive_enacted_interaction
        else:
            enacted_interaction = self._intended_interaction.increment(primitive_enacted_interaction,
                                                                       self._interactions)

        # If the intended interaction is determined (completely enacted or aborted)
        if enacted_interaction is not None:
            # Memorize the context
            self._penultimate_composite_interaction = self._previous_composite_interaction
            self._previous_composite_interaction = self._last_composite_interaction
            self._penultimate_interaction = self._previous_interaction
            self._previous_interaction = self._last_interaction
            self._last_interaction = enacted_interaction
            # Call the learning mechanism
            self.learn(enacted_interaction)
            # Create the proposed dataframe
            self.create_proposed_df()
            self.aggregate_propositions()
            # Decide the next enaction
            self.decide()
            self.enacted_length = 0

        # Trace
        self.trace_record["nb_schemas"] = len(self._interactions)

        # Return the next primitive action
        self._primitive_intended_interaction = self._intended_interaction.current()
        return self._primitive_intended_interaction.get_action()

    def learn(self, enacted_interaction):
        """Learn the composite interactions"""
        # First level of composite interactions
        self._last_composite_interaction = self.learn_composite_interaction(self._previous_interaction,
                                                                            enacted_interaction)
        # Second level of composite interactions
        self.learn_composite_interaction(self._previous_composite_interaction, enacted_interaction)
        self.learn_composite_interaction(self._penultimate_interaction, self._last_composite_interaction)

        # Higher level composite interaction made of two composite interactions
        if self._last_composite_interaction is not None:
            self.learn_composite_interaction(self._penultimate_composite_interaction, self._last_composite_interaction)

    def learn_composite_interaction(self, pre_interaction, post_interaction):
        """Record or reinforce the composite interaction made of (pre_interaction, post_interaction)"""
        if pre_interaction is None:
            return None
        else:
            # If the pre-interaction exists
            composite_interaction = CompositeInteraction(pre_interaction, post_interaction)
            if composite_interaction.key() not in self._interactions:
                # Add the composite interaction to memory
                self._interactions[composite_interaction.key()] = composite_interaction
                if TRACE:
                    print(f"Learning {composite_interaction}")
                return composite_interaction
            else:
                # Reinforce the existing composite interaction and return it
                self._interactions[composite_interaction.key()].reinforce()
                if TRACE:
                    print(f"Reinforcing {self._interactions[composite_interaction.key()]}")
                return self._interactions[composite_interaction.key()]

    def create_proposed_df(self):
        """Create the proposed dataframe from the activated interactions"""
        # The list of activated interactions that match the current context
        activated_interactions = [i for i in self._interactions.values() if i.get_length() > 1
                                  and i.pre_interaction in self._last_composite_interaction.get_post_interactions()]
        data = {'activated': [i.key() for i in activated_interactions],
                'weight': [i.weight for i in activated_interactions],
                'actions': [i.post_interaction.get_actions() for i in activated_interactions],
                'intention': [i.post_interaction.key() for i in activated_interactions],
                'valence': [i.post_interaction.get_valence() for i in activated_interactions],
                'decision': [i.post_interaction.get_decision() for i in activated_interactions],
                'pre': [i.post_interaction.pre_key() for i in activated_interactions],
                'length': [i.post_interaction.get_length() for i in activated_interactions],
                }
        activated_df = pd.DataFrame(data).astype(
            self._default_df.dtypes)  # Force the same types in case activated_df is empty

        # Create the proposed dataframe
        self.proposed_df = pd.concat(
            [self._default_df, activated_df], ignore_index=True).sort_values(by='decision',
                                                                             ascending=True).reset_index(drop=True)

        # Calculate the proclivity of each proposition
        self.proposed_df['proclivity'] = self.proposed_df['weight'] * self.proposed_df['valence']

    def aggregate_propositions(self):
        """Aggregate the proclivity"""
        # Aggregate the proclivity for each decision
        grouped_df = self.proposed_df.groupby('decision').agg(
            {'proclivity': 'sum', 'actions': 'first',  # 'action': 'first',
             'length': 'first', 'intention': 'first', 'pre': 'first'}).reset_index()
        # For each proposed composite decision
        for index, proposed in grouped_df[grouped_df['length'] > 1].iterrows():
            # print(f"Index {index}, actions {proposition['actions']}, intention {proposition['intention']}")
            # Find shorter decisions that start with the same sequence
            for _, shorter in self.proposed_df[
                self.proposed_df.apply(lambda row: proposed['actions'].startswith(row['actions'])
                                                   and row['length'] < proposed['length'], axis=1)].iterrows():
                # Add the proclivity of the shorter decisions
                grouped_df.loc[index, 'proclivity'] += shorter['proclivity']
                # print(f"Decision {proposed['decision']} recieves {shorter['proclivity']} from shorter {shorter['intention']}")

        # Remove the intentions that are insufficiently reinforced
        grouped_df = grouped_df[grouped_df['intention'].apply(lambda x: self._interactions[x].weight) >= MIN_WEIGHT]
        # Remove the intentions that are too long
        grouped_df = grouped_df[
            grouped_df['intention'].apply(lambda x: self._interactions[x].get_length()) <= MAX_LENGTH]

        # Sort by descending proclivity
        self.decision_df = grouped_df.sort_values(by=['proclivity', 'decision'], ascending=[False, True]).reset_index(
            drop=True)

    def decide(self):
        """Selects the intended_interaction at the top of the proposed dataframe"""
        # The intended interaction is in the first row because it has been sorted by descending proclivity
        intended_interaction_key = self.decision_df.loc[0, 'intention']
        if TRACE:
            print("Intention:", intended_interaction_key)
        self._intended_interaction = self._interactions[intended_interaction_key]
