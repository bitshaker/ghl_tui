# Contacts Search API

Please note: Due to the complexity of the advanced filtering requirements, updates may take a few seconds to appear in the search results.

The Contacts Search API enables users to search for contacts within your CRM system based on specified criteria. It offers extensive filtering, sorting, and pagination options to refine search results according to specific needs.

**Endpoint:** `POST /contacts/search`

## 🔸 Request Body

| **Parameter** | **Type** | **Required** | **Description** | **Example** |
| ---| ---| ---| ---| --- |
| `locationId` | string | Yes | Location ID in which the search needs to be performed. | `5DP41231LkQsiKESj6rh` |
| `page` | number | No | The page number of results to retrieve. Used for standard pagination. | `1` |
|  |  |  | ⚠️ **Note :** When using `searchAfter` parameter, `page` should not be provided. |  |
| `pageLimit` | number | Yes | The number of results to limit per page. | `20` |
| `searchAfter` | array | No | Used for cursor-based pagination. This value is returned in the response of each document and defines where to start the next page from. | `[10, "ABC"]` |
|  |  |  | ⚠️ **Note :** Required for retrieving results beyond 10,000 records. |  |
| `filters` | array | No |  |  |
| |---- `group` |  |  | Logical group operator for the filters. Must be either `AND` or `OR`. |  |
| |---- `filters` |  |  | Array of filters or nested filter groups to be grouped together. |  |
| |---- `field` |  |  | Name of the field to filter by. |  |
| |---- `operator` |  |  | Operator to apply for filtering. |  |
| |---- `value` |  |  | Value for the filter. |  |
|  |  |  | ⚠️ **Note :** By default every filter in the `filters` array is considered in `AND` logical group |  |
| `sort` | array | No | Array of sorting criteria to apply for ordering search results. |  |
| |---- `field` |  |  | Name of the field to sort by. |  |
| |---- `direction` |  |  | Sorting direction (`asc` for ascending, `desc` for descending). |  |
| `query` | string | No | The string you want to search for within your contacts. The results will depend on the searchable fields you’ve configured.<br><br>⚠️ **Note:**<br><br>limit<br><br>query<br><br>searchable<br><br>Custom Fields Settings<br><br><br>For more information on how searchable fields work for contacts, please refer to this guide:<br>[https://help.gohighlevel.com/support/solutions/articles/155000003913-searching-an-object-record](https://help.gohighlevel.com/support/solutions/articles/155000003913-searching-an-object-record)<br> |  |

### Pagination Limitations
The API has the following pagination limitations:

1. **Standard Pagination (page & pageLimit)**
    *   Can fetch a `maximum of 10,000 records` in total
    *   Use `page` and `pageLimit` parameters

**Note**:
The API with **Standard Pagination** supports retrieving up to 10,000 records in total, with a maximum of 500 records per request. To access all records, use the page and pageLimit parameters to paginate through results.
For example, `page=20` and `pageLimit=500` will provide you the last set of result set using pagination API.

* * *

1. **Cursor-based Pagination (searchAfter & pageLimit)**
    *   Required for accessing `more than 10,000 records`
    *   Use the `searchAfter` parameter returned in each response to fetch the next set of results
    *   `Do not include` the `page` parameter when using `searchAfter`
    *   This allows for efficient pagination through large result sets

#### Sample Request Body

```json
{
  "locationId": "5DP41231LkQsiKESj6rh",
  "page": 1,
  "pageLimit": 20,
  "searchAfter": ["bs5qhs78vqhs", "2FP41231LkQsiKESj6eg"],
  "filters": [
    {
       "field": "dnd",
       "operator": "eq",
       "value": true
    },

    {
      "group": "OR",
      "filters": [
        {
          "field": "firstNameLowerCase",
          "operator": "eq",
          "value": "alex"
        },
        {
          "field": "lastNameLowerCase",
          "operator": "eq",
          "value": "peter"
        }
      ]
    },
    
  ],
  "sort": [
    {
      "field": "firstNameLowerCase",
      "direction": "desc"
    }
  ],
 "query":"tom"
}
```

##   

## Filters

The Search Contacts API supports a variety of filters that allow users to refine their search results based on specific criteria. Filters can be applied individually or grouped together using logical operators (AND, OR) to create complex search queries each comprising three essential components:
1. **Field**: Indicates the attribute or property of contacts by which the filter is applied. For example, `contactName` refers to the name of the contact.
2. **Operator**: Specifies the operation to be performed on the field to filter contacts. Operators define the type of comparison or matching to be executed.
3. **Value**: Represents the specific value against which the field is compared using the specified operator. This value varies based on the filter criteria and can be a string, number, or other data type relevant to the field being filtered.

#### Sample Filter Payload

```json
{
  "filters": [
    {
      "group": "AND",
      "filters": [
        {
          "field": "firstNameLowerCase",
          "operator": "contains",
          "value": "John"
        },
        {
          "field": "email",
          "operator": "exists"
        }
      ]
    },
    {
      "group": "OR",
      "filters": [
        {
          "field": "city",
          "operator": "eq",
          "value": "New York"
        },
        {
          "field": "state",
          "operator": "eq",
          "value": "California"
        }
      ]
    }
  ]
}
```

#### Supported Filter Operators

| **Operator** | **Definition** | **Value Type** | Example | **Character**<br>**Limit**<br> |
| ---| ---| ---| ---| --- |
| eq | Equals | Number, String, Boolean | ![](https://t8631005.p.clickup-attachments.com/t8631005/d9c569e7-2238-4de1-a75c-3f5b32f2e1e8/image.png) | 75 |
| not\_eq | Not Equals | Number, String, Boolean | ![](https://t8631005.p.clickup-attachments.com/t8631005/d1ae1e3d-9b7e-4782-b42e-f32fd1d868b8/image.png) | 75 |
| contains | Contains | String `(The contains operator does not support special characters.)` | ![](https://t8631005.p.clickup-attachments.com/t8631005/0624521d-cf3a-49a2-93d9-b06984dbeb36/image.png) | 75 |
| not\_contains | Not Contains | String`(The not_contains operator does not support special characters.)` | ![](https://t8631005.p.clickup-attachments.com/t8631005/e137578d-7687-41f0-a8d6-66fd6245305e/image.png) | 75 |
| exists | Exists (has a value) | `Undefined`<br>`(Do not pass any value, just field and operator are enough)` | ![](https://t8631005.p.clickup-attachments.com/t8631005/81a7a1cf-cace-4beb-9af4-595ea0753407/image.png) | None |
| not\_exists | Does not exist (no value) | `Undefined`<br>`(Do not pass any value, just field and operator are enough)` | ![](https://t8631005.p.clickup-attachments.com/t8631005/174c6749-f6d5-4b18-b946-9f5f9d6a6c29/image.png) | None |
| range | Range | ![](https://t8631005.p.clickup-attachments.com/t8631005/f495ea7f-74da-49c5-bfa7-8e6ff61e0df2/image.png)<br><br>![](https://t8631005.p.clickup-attachments.com/t8631005/0c5738ee-cd9e-4e96-9be6-d674490d3878/image.png)<br> | ![](https://t8631005.p.clickup-attachments.com/t8631005/2328e5b4-2770-4e80-aecc-9ef5260c99a5/image.png) | 75 |

####   

#### Supported Filter Fields

| **Display Name** | **Field Name** | **Supported Operators** | **Example** |
| ---| ---| ---| --- |
| **Contact Information** |
| Contact Id | id<br> | eq<br>not\_eq | ![](https://t8631005.p.clickup-attachments.com/t8631005/cb410489-578e-4da2-806a-5a653a05ab12/image.png) |
| Contact Name | contactName | eq<br>not\_eq<br>exists<br>not\_exists | ![](https://t8631005.p.clickup-attachments.com/t8631005/5de13576-4b58-4578-a39d-17a979b68ab1/image.png) |
| Address | address | eq<br>not\_eq<br>contains<br>not\_contains<br>exists<br>not\_exists | ![](https://t8631005.p.clickup-attachments.com/t8631005/65b077f0-997b-4498-9a43-b5ae86532320/image.png) |
| Assigned | assignedTo | eq<br>not\_eq<br>exists<br>not\_exists | ![](https://t8631005.p.clickup-attachments.com/t8631005/a48d3751-72f1-4b09-962f-16b3d169b8a4/image.png) |
| Business Name | businessName | eq<br>not\_eq<br>contains<br>not\_contains<br>exists<br>not\_exists | ![](https://t8631005.p.clickup-attachments.com/t8631005/9e6e2103-5b32-4072-8ee9-901c43be5441/image.png) |
| City | city | eq<br>not\_eq<br>contains<br>not\_contains<br>exists<br>not\_exists | ![](https://t8631005.p.clickup-attachments.com/t8631005/0d36ca7f-e8c4-4c3a-8d5b-801ad1999d9a/image.png) |
| Country | country | eq<br>not\_eq<br>exists<br>not\_exists | ![](https://t8631005.p.clickup-attachments.com/t8631005/fbe62d83-4fee-4152-bd1f-5e8c951501b4/image.png) |
| Company Name | companyName | eq<br>not\_eq<br>contains<br>not\_contains<br>exists<br>not\_exists | ![](https://t8631005.p.clickup-attachments.com/t8631005/2a2db5df-8ac9-4b68-9465-5c0eedbe16ca/image.png) |
| Created At | dateAdded | range<br>exists<br>not\_exists | ![](https://t8631005.p.clickup-attachments.com/t8631005/eb9b0941-403d-4c67-b2bc-82affe468ad5/image.png) |
| Updated At | dateUpdated | range<br>exists<br>not\_exists<br> | ![](https://t8631005.p.clickup-attachments.com/t8631005/6f545fe1-9e15-4bfe-aed0-350c92eec4e6/image.png) |
| DND | dnd | eq<br>not\_eq<br>exists<br>not\_exists | ![](https://t8631005.p.clickup-attachments.com/t8631005/b3c3a57f-62ab-4f6c-9623-8d0bf1ce6122/image.png) |
| Email | email | eq<br>not\_eq<br>exists<br>not\_exists<br><br>`contains and not_contains are not yet supported` | ![](https://t8631005.p.clickup-attachments.com/t8631005/15452ea0-fbb5-4930-8cda-38f816322d1f/image.png) |
| Followers | followers | eq<br>not\_eq<br>exists<br>not\_exists | ![](https://t8631005.p.clickup-attachments.com/t8631005/bd8f09f6-9458-40fe-8cd7-c09dca925b6d/image.png)![](https://t8631005.p.clickup-attachments.com/t8631005/03a4a427-e602-4ecc-bb33-0b98a4dba2bb/image.png) |
| First Name Lower Case | firstNameLowerCase<br> | eq<br>not\_eq<br>contains<br>not\_contains<br>exists<br>not\_exists | ![](https://t8631005.p.clickup-attachments.com/t8631005/f829488a-7aa5-4bfb-a9d5-11f814afb884/image.png) |
| First Name (Without Lower Case) | `Coming soon!` | `Coming soon!` | `Coming soon!` |
| Last Name Lower Case | lastNameLowerCase | eq<br>not\_eq<br>contains<br>not\_contains<br>exists<br>not\_exists | ![](https://t8631005.p.clickup-attachments.com/t8631005/2ff49c49-ae0e-4f1f-9b71-20be3b2619f6/image.png) |
| Last Name (Without Lower Case) | `Coming soon!` | `Coming soon!` | `Coming soon!` |
| Is Valid Whatsapp | isValidWhatsapp | eq<br>not\_eq<br>exists<br>not\_exists | ![](https://t8631005.p.clickup-attachments.com/t8631005/85d80e5e-d41a-480a-afa7-5f15f9c25899/image.png) |
| Last Email Clicked Date | lastEmailClickedDate | range<br>exists<br>not\_exists | ![](https://t8631005.p.clickup-attachments.com/t8631005/bf044ccb-efd1-4cfe-a424-14a50bff2df7/image.png) |
| Last Email Opened Date | lastEmailOpenedDate | range<br>exists<br>not\_exists | ![](https://t8631005.p.clickup-attachments.com/t8631005/d5bfbc8a-481d-4970-8b9b-b61c6d223783/image.png) |
| Phone<br>(Do pass in the correct country code)<br>Eg: `+91701000000` | phone | eq<br>not\_eq<br>contains<br>not\_contains<br>exists<br>not\_exists | ![](https://t8631005.p.clickup-attachments.com/t8631005/5c9074e1-7c6e-4e1b-a8ec-4a488a55f3c8/image.png) |
| Postal Zip Code | postalCode | eq<br>not\_eq<br>contains<br>not\_contains<br>exists<br>not\_exists | ![](https://t8631005.p.clickup-attachments.com/t8631005/8f9038f8-8a7d-49ec-95df-f1e11bf2e467/image.png) |
| Source | source | eq<br>not\_eq<br>contains<br>not\_contains<br>exists<br>not\_exists | ![](https://t8631005.p.clickup-attachments.com/t8631005/ac8f5454-5357-4259-8081-51b20371e783/image.png) |
| State | state | eq<br>not\_eq<br>contains<br>not\_contains<br>exists<br>not\_exists | ![](https://t8631005.p.clickup-attachments.com/t8631005/2f10091f-51ed-4788-8f71-1b55e650cd78/image.png) |
| Tags | tags | eq<br>not\_eq<br>contains<br>not\_contains<br>exists<br>not\_exists | ![](https://t8631005.p.clickup-attachments.com/t8631005/33d5dc41-3ce1-4ee7-97ef-cadc9aa5ec14/image.png)![](https://t8631005.p.clickup-attachments.com/t8631005/256ad967-7e02-47b5-b9d0-0c876edd538a/image.png) |
| Timezone<br>Eg: `Pacific/Honolulu` | timezone | eq<br>not\_eq<br>exists<br>not\_exists | ![](https://t8631005.p.clickup-attachments.com/t8631005/439dda58-c2e0-46ac-a9ad-21f7c9ee8172/image.png) |
| Contact Type | type | eq<br>not\_eq<br>exists<br>not\_exists | ![](https://t8631005.p.clickup-attachments.com/t8631005/7e733636-e941-4c18-81b4-9351e209b9cc/image.png) |
| Is Valid Email<br>(Applicable only if Email Validation is enabled for the location) | validEmail | eq<br>not\_eq<br>exists<br>not\_exists | ![](https://t8631005.p.clickup-attachments.com/t8631005/b7ec4632-68cb-493d-9867-194822e80384/image.png) |
| Website | website | eq<br>not\_eq<br>exists<br>not\_exists<br><br>`contains and not_contains are not yet supported` | ![](https://t8631005.p.clickup-attachments.com/t8631005/ba22577e-aa96-4946-803f-ba54fbbf458b/image.png) |
| Date of Birth | dateOfBirth | range<br>exists<br>not\_exists<br> | ![](https://t8631005.p.clickup-attachments.com/t8631005/f5c9f088-eece-40cd-b415-d49a6526f19a/Screenshot%202025-11-19%20at%205.41.51%E2%80%AFPM.png) |
| **Contact Activity** |
|  |
| Last Appointment - Confirmed/Open | lastAppointment | range<br>exists<br>not\_exist | ![](https://t8631005.p.clickup-attachments.com/t8631005/2e30c399-6945-46ea-9931-b5bd1ab3bdee/image.png) |
| Workflow (Active) | activeWorkflows | eq<br>not\_eq<br>exists<br>not\_exists | ![](https://t8631005.p.clickup-attachments.com/t8631005/9013e6ca-b9a7-4b22-9654-04f76592f51e/image.png) |
| Workflow (Finished) | finishedWorkflows | eq<br>not\_eq<br>exists<br>not\_exists | ![](https://t8631005.p.clickup-attachments.com/t8631005/568f0638-ede0-4549-a3ac-7566b3df8a86/image.png) |
| **Opportunity Information** |
| Pipeline | **field** - `opportunities`<br>**sub field** \- `pipelineId` | **field** - nested<br><br>**sub field** \-<br>eq<br>not\_eq<br>exists<br>not\_exists | ![](https://t8631005.p.clickup-attachments.com/t8631005/7f511802-6d2d-45a4-baf5-7a33de43d981/image.png) |
| Pipeline Stage | **field** - `opportunities`<br>**sub field** \- `pipelineStageId` | **field** - nested<br><br>**sub field** \-<br>eq<br>not\_eq<br>exists<br>not\_exists | ![](https://t8631005.p.clickup-attachments.com/t8631005/49a88420-63e7-4707-949a-112145446555/image.png) |
| Pipeline Status | **field** - `opportunities`<br>**sub field** \- `status` | **field** - nested<br><br>**sub field** \-<br>eq<br>not\_eq<br>exists<br>not\_exists | ![](https://t8631005.p.clickup-attachments.com/t8631005/32b2cf8b-b5b6-4a92-9621-b387c6425e4a/image.png) |
| Opportunities Combination Filters | You can combine 2 or more sub-fields under opportunities nested filters |  | ![](https://t8631005.p.clickup-attachments.com/t8631005/a2620450-6b2d-40ad-9df5-beb278504410/image.png) |
| **Custom Fields** |
| _TEXT_<br><br>_LARGE\_TEXT_<br><br>_SINGLE\_OPTIONS_<br><br>_RADIO_<br><br>_PHONE_<br><br> | <br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br>`customFields.`_`{{ custom_field_id }}`_<br>Eg: `customFields.OBj007JIEmLP0IEHdV1l`<br> | eq<br>not\_eq<br>contains<br>not\_contains<br>exists<br>not\_exists<br> | ![](https://t8631005.p.clickup-attachments.com/t8631005/62a3c1ed-3f83-4314-896a-5201426f842e/image.png)![](https://t8631005.p.clickup-attachments.com/t8631005/0870200a-20bd-4718-bedf-79b478bd562d/image%20(1).png) |
| _CHECKBOX_<br><br>_MULTIPLE\_OPTIONS_<br><br> | eq<br>not\_eq<br>exists<br>not\_exists | ![](https://t8631005.p.clickup-attachments.com/t8631005/dece57d5-f8a3-4211-b744-6c1cad52c8fd/image.png)![](https://t8631005.p.clickup-attachments.com/t8631005/b2bf00c5-9f01-4cd3-9227-dbf282d2c91b/image.png) |
| _NUMERICAL_<br><br>_MONETORY_<br><br> | range<br>exists<br>not\_exists<br>eq<br>not\_eq | ![](https://t8631005.p.clickup-attachments.com/t8631005/f97edbe2-3271-41f0-8bbf-4342b7c6bedb/image.png)![](https://t8631005.p.clickup-attachments.com/t8631005/36107864-3e6d-4d2f-8559-9bb3e4342697/image.png) |
| _DATE_<br><br> | range<br>exists<br>not\_exists | ![](https://t8631005.p.clickup-attachments.com/t8631005/1e884f25-c225-4f6d-b799-0447b4137e19/image.png) |
| _TEXTBOX\_LIST_<br><br> | `customFields.`_`{{ custom_field_id }}.{{ optionoption_id }}`_<br>Eg: `customFields.OBj007JIEmLP0IEHdV1l.c1b70ec9-664f-400f-a3fc-6f7912c5e310`<br><br> | eq<br>not\_eq<br>contains<br>not\_contains<br>exists<br>not\_exists | ![](https://t8631005.p.clickup-attachments.com/t8631005/473b83b0-3da9-4039-afbc-8eb3e29a65bc/Screenshot%202024-07-23%20at%202.53.15%E2%80%AFPM.png) |

### **Sort**

The Search Contacts API supports sorting contacts based on various fields. Users can specify the field to sort by, the sorting direction (ascending or descending), and whether the field is a custom field.
1. **Field**: Indicates the attribute or property of contacts by which the sorting is applied. For example, "date\_of\_birth" represents the birth date of the contact.
2. **Direction**: Specifies the sorting direction as either "asc" (ascending) or "desc" (descending).
3. **Is Custom Field**: Indicates whether the field being sorted is a custom field.

#### Sample Sort Payloads
Note: `You can combine 2 sort at once`

```json
[
  {
    "field": "dateAdded",
    "direction": "desc"
  },
  {
    "field": "firstNameLowerCase",
    "direction": "asc"
  }
]
```

#### Supported Fields

| **Display Name** | **Field Name** | Example |
| ---| ---| --- |
| First Name (Lowercase) | firstNameLowerCase | ![](https://t8631005.p.clickup-attachments.com/t8631005/da4d95e1-f109-4071-af7b-f19bd0b75488/image.png) |
| Last Name (Lowercase) | lastNameLowerCase | ![](https://t8631005.p.clickup-attachments.com/t8631005/5b7cc85a-ce2d-4eaf-be73-394fbd724a5a/image.png) |
| Business Name | businessName | ![](https://t8631005.p.clickup-attachments.com/t8631005/d3210cc1-580f-4cea-a5a8-1b004f091cd4/image.png) |
| Date Created | dateAdded | ![](https://t8631005.p.clickup-attachments.com/t8631005/efd46e19-7885-429e-99f0-38bbe405142a/image.png) |
| Date Updated | dateUpdated | ![](https://t8631005.p.clickup-attachments.com/t8631005/bb3881ab-02de-4cca-97c8-b0128b56fecb/image.png) |
| Email | email | ![](https://t8631005.p.clickup-attachments.com/t8631005/0f709ee0-f4b9-4cb6-b610-dafbb8e173dd/image.png) |
| DND | dnd | ![](https://t8631005.p.clickup-attachments.com/t8631005/34bb03c9-ae51-4039-8552-acd90db42776/image.png) |
| Source | source | ![](https://t8631005.p.clickup-attachments.com/t8631005/065504ec-29ed-4524-b101-461e7d570211/image.png) |

### Response Body

```json
{
  "contacts": [
    {
      "id": "102goXVW3lIExEQPOnd3",
      "additionalEmails": ["john@example.com", "jane@example.com"],
      "additionalPhones": ["123456789", "987654321"],
      "address": "123 Main Street",
      "assignedTo": "182goXVW3lIExEQPOnd3",
      "businessId": "282goXVW3lIExEQPOnd3",
      "businessName": "Acme Corporation",
      "city": "New York",
      "companyName": "XYZ Corp",
      "country": "United States",
      "customFields": [
          { 
            "id": "sqoiOo5mAb8qwjXvcgdQ",
            "value": "random",
          }
          { 
            "id": "qweqgehuqwejqeiqwoqw",
            "value": ["option - 1", "option -2"],
          }
      ],
      "dateAdded": "2024-06-06T18:54:57.221Z",
      "dateOfBirth": "1990-01-01",
      "dateUpdated": "2024-06-06T18:54:57.221Z",
      "dnd": false,
      "dndSettings": {},
      "email": "john@example.com",
      "firstNameLowerCase": "john", // first name without lowercase is not yet available.
      "lastNameLowerCase": "doe", // first name without lowercase is not yet available.
      "followers": ["682goXVW3lIExEQPOnd3", "582goXVW3lIExEQPOnd3"],
      "locationId": "502goXVW3lIExEQPOnd3",
      "phone": "+123456789",
      "phoneLabel": "Mobile",
      "postalCode": "12345",
      "source": "Website",
      "state": "California",
      "tags": ["tag-1", "tag-2"],
      "type": "lead",
      "validEmail": true,
      "website": "www.example.com",
      "attributionSource": {
          "utmSource": "google",
          "utmKeyword": "crm platform",
          "utmTerm": "crm+tool",
          "utmMatchtype": "b",
          "sessionSource": "google_ads",
          "medium": "paid",
          "mediumId": "md_123",
          "campaign": "winter_sale",
          "utmMedium": "cpc",
          "utmContent": "banner_1",
          "gclid": "EAIaIQobChMI12",
          "fbclid": "fb.12345.abc",
          "campaignId": "cmp_789",
          "adId": "ad_456",
          "adGroupId": "adg_321",
          "referrer": "https://example.com",
          "fbc": "fb.1.123.456",
          "fbp": "fbp.1.789.321",
          "userAgent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
          "ip": "192.168.1.10",
          "gaClientId": "12345.67890",
          "adName": "crm_ad_set",
          "gbraid": "gbraid_sample_123",
          "wbraid": "wbraid_sample_456",
          "url": "https://product.com/pricing",
          "adSource": "google_ads"
      },
    "lastAttributionSource": {
        "utmSource": "facebook",
        "utmKeyword": "marketing automation",
        "utmTerm": "automation+tool",
        "utmMatchtype": "e",
        "sessionSource": "facebook_ads",
        "medium": "social",
        "mediumId": "md_987",
        "campaign": "new_year_blast",
        "utmMedium": "paid_social",
        "utmContent": "video_ad",
        "gclid": "EAIaIQobChMI99",
        "fbclid": "fb.67890.xyz",
        "campaignId": "cmp_222",
        "adId": "ad_999",
        "adGroupId": "adg_555",
        "referrer": "https://facebook.com",
        "fbc": "fb.1.987.654",
        "fbp": "fbp.1.555.666",
        "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "ip": "203.0.113.15",
        "gaClientId": "98765.43210",
        "adName": "fb_lead_gen",
        "gbraid": "gbraid_sample_789",
        "wbraid": "wbraid_sample_999",
        "url": "https://landingpage.com/signup",
        "adSource": "facebook_ads"
      }
    }
  ],
  "total": 120
}
```

Association & Relations:

To fetch related objects, please refer to the documentation below:
Fetch Related Record By Id ([https://doc.clickup.com/d/h/87cpx-293776/cd0f4122abc04d3/87cpx-490276](https://doc.clickup.com/d/h/87cpx-293776/cd0f4122abc04d3/87cpx-490276))