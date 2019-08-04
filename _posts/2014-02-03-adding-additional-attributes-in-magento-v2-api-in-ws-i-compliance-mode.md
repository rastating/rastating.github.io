---
layout: post
title: "Adding Additional Attributes in Magento v2 API in WS-I Compliance Mode"
date: 2014-02-03 11:00:00 +0100
categories:
  - programming
tags:
  - magento
  - additional_attributes
  - ws-i
  - api
---
If you are trying to integrate with Magento using the v2 API in WS-I compliance mode, you're going to soon realise that any additional attributes you specify when calling the `catalogProductCreate` method are not going to show up in the product you create; as I so frustratingly found out after a good few hours of debugging!

The reason for this is due to a mistake that has been made in the WSDL for the WS-I compliant API. The definition of the `additional_attributes` element in the non WS-I compliant API (i.e. the one that doesn't suffer from this problem) is as follows:

```xml
<element name="additional_attributes" type="typens:catalogProductAdditionalAttributesEntity" minOccurs="0"/>
```

However, in the WS-I compliant WDSL, the definition is:

```xml
<xsd:element name="additional_attributes" type="typens:associativeArray" minOccurs="0">
</xsd:element>
```

The latter will generate XML which contains an array of associative entities within the additional_attributes element, as per the extract below:

```xml
<additional_attributes>
    <complexObjectArray>
        <key>
            shipping_international_economy
        </key>
        <value>
            10.0000
        </value>
    </complexObjectArray>
    <complexObjectArray>
        <key>
            shipping_rm_europe_sign
        </key>
        <value>
            10.0000
        </value>
    </complexObjectArray>
    <complexObjectArray>
        <key>
            shipping_rm_international_sign
        </key>
        <value>
            12.0000
        </value>
    </complexObjectArray>
</additional_attributes>
```

How this should actually appear is with a `single_data` or `multi_data` element as a direct child of the `additional_attributes` element.

Below is a snippet from the file that handles the API requests (found in `app/code/core/Mage/Catalog/Model/Product/Api/V2.php` on line 250) which deals with parsing the additional attributes:

```php
if (property_exists($productData, 'additional_attributes')) {
    if (property_exists($productData->additional_attributes, 'single_data')) {
        foreach ($productData->additional_attributes->single_data as $_attribute) {
            $_attrCode = $_attribute->key;
            $productData->$_attrCode = $_attribute->value;
        }
    }
    if (property_exists($productData->additional_attributes, 'multi_data')) {
        foreach ($productData->additional_attributes->multi_data as $_attribute) {
            $_attrCode = $_attribute->key;
            $productData->$_attrCode = $_attribute->value;
        }
    }

    unset($productData->additional_attributes);
}
```

As you can see, if the `single_data` or `multi_data` elements do not exist, it simply discards the data we pass to it.

In order to make this work with the WS-I compliant API, we simply need to add a third if statement to the above code to make it recognise there being an array of entities as a child of `additional_attributes`, which makes the above block look like this:

```php
if (property_exists($productData, 'additional_attributes')) {
    if (property_exists($productData->additional_attributes, 'single_data')) {
        foreach ($productData->additional_attributes->single_data as $_attribute) {
            $_attrCode = $_attribute->key;
            $productData->$_attrCode = $_attribute->value;
        }
    }
    if (property_exists($productData->additional_attributes, 'multi_data')) {
        foreach ($productData->additional_attributes->multi_data as $_attribute) {
            $_attrCode = $_attribute->key;
            $productData->$_attrCode = $_attribute->value;
        }
    }

    if (gettype($productData->additional_attributes) == 'array') {
        foreach ($productData->additional_attributes as $k => $v) {
            $_attrCode = $k;
            $productData->$_attrCode = $v;
        }
    }

    unset($productData->additional_attributes);
}
```

Make this modification to your V2.php file and you should see all your product creation requests working properly now instead of discarding the data you pass into the additional attributes. Alternatively, if you'd rather not patch it yourself, you can grab a copy of the patched file [From This Link](https://drive.google.com/open?id=1GViC7Gv7lYJAlLcZbKKW6ZBv4X5qpaEN).
