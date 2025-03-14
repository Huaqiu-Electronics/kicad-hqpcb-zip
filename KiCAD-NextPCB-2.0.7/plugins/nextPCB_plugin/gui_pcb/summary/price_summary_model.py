from dataclasses import dataclass
import wx.dataview as dv
from .bom_price_model import BomPriceModel
from .pcb_price_model import PCBPriceModel
from .smt_price_model import SmtPriceModel
from .price_model_base import PriceModelCol
from .price_model_base import PriceModelBase, PriceItem
from enum import Enum
from nextPCB_plugin.settings_nextpcb.setting_manager import SETTING_MANAGER


class PriceCategoryNextpcb(Enum):
    PCB = "pcb"
    SMT = "smt"



PRICE_KIND = 2


@dataclass
class PriceSummary:
    pcb_quantity: int = 0
    days: int = 0
    cost: int = 0


class PriceSummaryModel(dv.PyDataViewModel):
    def __init__(self  , models : 'dict[ int,PriceModelBase ]'):
        dv.PyDataViewModel.__init__(self)
        self.UseWeakRefs(True)
        # self.price_category: "dict[int,PriceModelBase]" = {
        #     PriceCategoryNextpcb.PCB: PCBPriceModel(),
        #     PriceCategoryNextpcb.SMT: SmtPriceModel(),
        # }
        self.price_category = models
        self._days_cost = 0
        self._pcb_quantity = 0
        self.row_item_mapping = []  # Maintain a mapping of row index to item

    @property
    def day_cost(self):
        return self._days_cost

    @property
    def pcb_count(self):
        return self._pcb_quantity

    def update_price(self, price: "dict"):
        # for i in PriceCategoryNextpcb.PCB, PriceCategoryNextpcb.SMT, PriceCategoryNextpcb.BOM:
        print(f"{PriceCategoryNextpcb.SMT.value}")
        # if  PriceCategoryNextpcb.SMT.value 
        # for i in PriceCategoryNextpcb.PCB, PriceCategoryNextpcb.SMT:
        for i in self.price_category:
            if i.value in price:
                self.price_category[i].update(price[i.value])
        self.Cleared()

    def get_sum(self):
        s = 0
        for i in self.price_category:
            s = s + self.price_category[i].sum()
        return s

    def GetColumnCount(self):
        return PriceModelCol.COL_COUNT

    def GetColumnType(self, col):
        mapper = {
            0: "string",
            1: "string",
        }
        return mapper[col]

    def GetChildren(self, parent, children, hideSmt = True):
        if not parent:
            for cat in self.price_category:
                if cat.value == 'smt':
                    children.append(self.ObjectToItem(self.price_category[cat]))
                    return PRICE_KIND
                children.append(self.ObjectToItem(self.price_category[cat]))
            return 1
        

        # Otherwise we'll fetch the python object associated with the parent
        # item and make DV items for each of its child objects.
        node = self.ItemToObject(parent)
        if node is None:
            return
        if isinstance(node, PriceModelBase):
            for i in node.get_items():
                item = self.ObjectToItem(i)
                children.append(item)
            return len(node.get_items())
        return 0


    # def add_custom_children(self, parent, hideSmt):
    #     """
    #     Add different children based on custom logic using GetChildren().
    #     """
    #     children = []

    #     # Call GetChildren() to populate children list
    #     self.GetChildren(parent, children, hideSmt)

    #     # # Custom logic to add or modify children based on hideSmt parameter
    #     # if not parent:
    #     #     for cat in self.price_category:
    #     #         # Check if hideSmt is True and the category is SMT, skip appending the child
    #     #         if hideSmt and cat == PriceCategoryNextpcb.SMT:
    #     #             continue
    #     #         children.append(self.ObjectToItem(self.price_category[cat]))
    #     # else:
    #     #     # Custom logic for modifying children based on parent
    #     #     # Add other conditions as needed for different parent types
    #     #     pass

    #     return children
    
    
    def IsContainer(self, item):
        # Return True if the item has children, False otherwise.
        ##self.log.write("IsContainer\n")

        # The hidden root is a container
        if not item:
            return True
        # and in this model the genre objects are containers
        node = self.ItemToObject(item)
        if isinstance(node, PriceModelBase):
            return True
        # but everything else (the song objects) are not
        return False

    # def HasContainerColumns(self, item):
    #    self.log.write('HasContainerColumns\n')
    #    return True

    def GetParent(self, item):
        # Return the item which is this item's parent.
        ##self.log.write("GetParent\n")

        if not item:
            return dv.NullDataViewItem

        node = self.ItemToObject(item)
        if isinstance(node, PriceModelBase):
            return dv.NullDataViewItem
        elif isinstance(node, PriceItem):
            return self.ObjectToItem(node.parent)
        return dv.NullDataViewItem

    def HasValue(self, item, col):
        # Overriding this method allows you to let the view know if there is any
        # data at all in the cell. If it returns False then GetValue will not be
        # called for this item and column.
        # if item is None:
        #     return
        if int(item.GetID()) == 1:
            return False

        # print(f"{int(item.GetID())}")
        node = self.ItemToObject(item)
        
        if isinstance(node, PriceModelBase) or isinstance(node, PriceItem):
            return True
        return False

    def GetValue(self, item, col):
        # Return the value to be displayed for this item and column. For this
        # example we'll just pull the values from the data objects we
        # associated with the items in GetChildren.

        # Fetch the data object for this item.
        if int(item.GetID()) == 1:
            return False
        node = self.ItemToObject(item)

        if isinstance(node, PriceModelBase):
            # Due to the HasValue implementation above, GetValue should only
            # be called for the first column for PriceModelBase objects. We'll verify
            # that with this assert.
            if 0 == col:
                return node.name()
            else:
                return f"{node.sum()}{SETTING_MANAGER.get_price_unit()}"

        elif isinstance(node, PriceItem):
            mapper = {
                0: node.desc,
                1: f"{node.value}{SETTING_MANAGER.get_price_unit()}",
            }
            return mapper[col]

        else:
            raise RuntimeError("unknown node type")

    def GetAttr(self, item, col, attr):
        ##self.log.write('GetAttr')
        if int(item.GetID()) == 1:
            return False
        node = self.ItemToObject(item)
        if (
            isinstance(node, PCBPriceModel)
            or isinstance(node, SmtPriceModel)
            # or isinstance(node, BomPriceModel)
        ):
            attr.SetColour("blue")
            attr.SetBold(True)
            return True
        return False

    def clear_content(self):
        # for i in PriceCategoryNextpcb.PCB, PriceCategoryNextpcb.SMT,:
        #     self.price_category[i].clear()
        # self.Cleared()
        pass

    def set_visibility(self, visibility):
        for i in PriceCategoryNextpcb.PCB, PriceCategoryNextpcb.SMT,:
            self.price_category[i].set_visibility(visibility)
        # self.visible = visibility
        