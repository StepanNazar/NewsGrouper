import inspect
from dataclasses import dataclass, field
from typing import ClassVar, TypeVar

T = TypeVar("T", bound="SubclassRegistrar")


@dataclass
class BaseClassConfig[T]:
    required_attrs: list[str]
    base_name: str
    subclasses: dict[str, type[T]] = field(default_factory=dict)


class SubclassRegistrar[T]:
    """Abstract base class for registering subclasses with required attributes and searching subclasses by name.

    Direct subclasses of this class are considered base classes and must define required class attributes using
    type annotations. When a non-abstract subclass of base class is defined, it is automatically registered, and
    it must define all required attributes and a unique 'name' attribute. "name" attribute should be a string and
    unique among all subclasses of the same base class.


    >>> from abc import ABC, abstractmethod
    >>> class NewsParser(SubclassRegistrar):
    ...     name: str
    ...     description: str
    ...     link_hint: str
    ...     # other attributes which are not required for children to define
    ...     other_attr: int = 42
    ...
    >>> class RedditParser(NewsParser):
    ...     name = "Reddit"
    ...     description = "Parser for Reddit posts"
    ...     link_hint = "https://www.reddit.com/r/your_subreddit"
    ...
    >>> [[parser.name, parser.description, parser.link_hint] for parser in NewsParser.get_all_subclasses()]
    [['Reddit', 'Parser for Reddit posts', 'https://www.reddit.com/r/your_subreddit']]
    >>> NewsParser.get_subclass_by_name("Reddit").name
    'Reddit'
    >>> NewsParser.get_subclass_by_name("NonExistentParser")
    Traceback (most recent call last):
        ...
    ValueError: NewsParser with name 'NonExistentParser' not found
    >>> class AnotherRedditParser(RedditParser):
    ...     name = "AnotherReddit"
    ...     description = "Another parser for Reddit posts"
    ...     link_hint = "https://www.reddit.com/r/another_subreddit"
    ...
    >>> class AnotherRedditParserDuplicate(NewsParser):
    ...     name = "AnotherReddit"
    ...     description = "Another parser for Reddit posts"
    ...     link_hint = "https://www.reddit.com/r/another_subreddit"
    Traceback (most recent call last):
        ...
    ValueError: NewsParser name 'AnotherReddit' is not unique among subclasses
    >>> class NotAllAttrsParser(NewsParser):
    ...     name = "IncompleteParser"
    ...     description = "This parser is missing the link_hint attribute"
    Traceback (most recent call last):
        ...
    TypeError: NotAllAttrsParser must define class attribute 'link_hint'
    >>> class NotRegisteredParser(RedditParser, ABC):
    ...     @abstractmethod
    ...     def some_abstract_method(self):
    ...         pass
    ...
    >>> NewsParser.get_all_subclasses()
    [<class '__main__.RedditParser'>, <class '__main__.AnotherRedditParser'>]
    >>> class AnotherBase(SubclassRegistrar):
    ...     name: str
    ...     description: str
    ...
    >>> class AnotherImplementation(AnotherBase):
    ...     name = "AnotherImpl"
    ...     description = "Implementation of another base class"
    ...
    >>> AnotherBase.get_all_subclasses()
    [<class '__main__.AnotherImplementation'>]
    >>> NewsParser.get_all_subclasses()
    [<class '__main__.RedditParser'>, <class '__main__.AnotherRedditParser'>]
    """

    _base_classes_config: ClassVar[
        dict[type["SubclassRegistrar"], BaseClassConfig]
    ] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if SubclassRegistrar._is_base_class(cls):
            cls._register_base_class()
        elif not inspect.isabstract(cls):
            cls._validate_and_register_subclass()

    @classmethod
    def _register_base_class(cls):
        required_attrs = list(set(cls.__annotations__) - set(cls.__dict__))
        if "name" not in required_attrs:
            required_attrs.append("name")
        SubclassRegistrar._base_classes_config[cls] = BaseClassConfig[T](
            required_attrs=required_attrs,
            base_name=cls.__name__,
        )

    @staticmethod
    def _is_base_class(class_):
        return SubclassRegistrar in class_.__bases__

    @classmethod
    def _validate_and_register_subclass(cls):
        base_class_config = cls._get_base_class_config()
        for attr in base_class_config.required_attrs:
            cls._require_attr(attr)
        cls._require_attr("name")
        if cls.name in base_class_config.subclasses:  # type: ignore
            raise ValueError(
                f"{base_class_config.base_name} name '{cls.name}' is not unique among subclasses"  # type: ignore
            )
        base_class_config.subclasses[cls.name] = cls  # type: ignore

    @classmethod
    def _get_base_class_config(cls) -> BaseClassConfig:
        for parent in cls.__mro__:
            if SubclassRegistrar._is_base_class(parent):
                return SubclassRegistrar._base_classes_config[parent]
        raise TypeError(
            f"{cls.__name__} does not have a registered base class in its hierarchy"
        )

    @classmethod
    def _require_attr(cls, attr: str):
        if not hasattr(cls, attr):
            raise TypeError(f"{cls.__name__} must define class attribute '{attr}'")

    @classmethod
    def get_all_subclasses(cls) -> list[type[T]]:
        """Get all registered subclasses which are not abstract."""
        return list(SubclassRegistrar._base_classes_config[cls].subclasses.values())

    @classmethod
    def get_subclass_by_name(cls, name: str) -> type[T]:
        """Get a subclass by its name."""
        subclass = SubclassRegistrar._base_classes_config[cls].subclasses.get(name)
        if subclass:
            return subclass
        base_name = SubclassRegistrar._base_classes_config[cls].base_name
        raise ValueError(f"{base_name} with name '{name}' not found")


if __name__ == "__main__":
    import doctest

    doctest.testmod()
